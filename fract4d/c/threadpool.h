/* Thread Pool routines originally pilfered from "Pthreads
   Programming", Nichols, Buttlar & Farrell, O'Reilly 

   I've minimally C++-ized them (added ctors etc), and converted from
   a linked list to to a templated array. This has the advantage that
   we don't need to call new() to introduce new work items.

*/

#ifndef _THREADPOOL_H_
#define _THREADPOOL_H_

#include "pthread.h"
#include <signal.h>
#include <cassert>
#include <limits.h>
#include <iostream>

/* one unit of work */
template<class work_t, class threadInfo>
struct tpool_work {
    void (*routine)(work_t&, threadInfo *); /* pointer to func which will do work */
    work_t arg; /* arguments */
};

/* argument passed to new thread - pointer to threadInfo instance
   + pointer to threadpool proper */
template<class T>
struct tpool_threadInfo {
    void *pool; /* can't work out how to declare this right now */
    T *info;
};

/* templatized on the unit of work and the type which holds per-thread info */
template<class work_t, class threadInfo>
class tpool {
 public:
    tpool(int num_worker_threads_, int max_queue_size_, threadInfo *tinfo_)
        {
            num_threads = num_worker_threads_;
            max_queue_size = max_queue_size_;
            tinfo = new tpool_threadInfo<threadInfo>[num_threads];
            
            for(int i = 0; i < num_worker_threads_; ++i)
            {
                tinfo[i].pool = this;
                tinfo[i].info = &tinfo_[i];
            }
            queue = new tpool_work<work_t,threadInfo>[max_queue_size];
            threads = new pthread_t[num_threads];
            
            cur_queue_size = 0;
            queue_head = 0;
            queue_tail = 0;
            queue_closed = 0;
            shutdown = 0;

            total_work_done = -num_threads;
            target_work_done = INT_MAX;
            work_queued = 0;

            pthread_mutex_init(&queue_lock, NULL);
            pthread_cond_init(&queue_not_empty, NULL);
            pthread_cond_init(&queue_not_full, NULL);
            pthread_cond_init(&queue_empty, NULL);
            pthread_cond_init(&queue_work_complete, NULL);

            /* create low-priority attribute block */
            pthread_attr_t lowprio_attr;
            //struct sched_param lowprio_param;
            pthread_attr_init(&lowprio_attr);
            //lowprio_param.sched_priority = sched_get_priority_min(SCHED_OTHER);
            //pthread_attr_setschedparam(&lowprio_attr, &lowprio_param);

            for(int i = 0; i < num_threads; ++i)
            {
                pthread_create(&threads[i], &lowprio_attr, 
                               (void *(*)(void *))&threadFunc, &tinfo[i]);
            }
        }
    
    ~tpool()
        {
            pthread_mutex_lock(&queue_lock);
            queue_closed = 1;

            /* wait for the queue to empty */
            while(cur_queue_size != 0)
            {
                pthread_cond_wait(&queue_empty,&queue_lock);
            }
            
            shutdown = 1;
            
            pthread_mutex_unlock(&queue_lock);
            
            /* wake up any sleeping workers */
            pthread_cond_broadcast(&queue_not_empty);
            pthread_cond_broadcast(&queue_not_full);
            
            for(int i = 0; i < num_threads; ++i)
            {
                pthread_join(threads[i],NULL);
            }
            
            delete[] threads;
            delete[] queue;
            delete[] tinfo;
        }

    static void threadFunc(tpool_threadInfo<threadInfo> *pinfo)
        {
	    tpool<work_t,threadInfo> *p = 
		(tpool<work_t,threadInfo> *) pinfo->pool;

	    p->work(pinfo->info);
        }

    int add_work(void (*routine)(work_t&, threadInfo *), const work_t& arg)
        {
            pthread_mutex_lock(&queue_lock);
            
            while((cur_queue_size == max_queue_size) &&
                  (!(shutdown || queue_closed)))
            {
                pthread_cond_wait(&queue_not_full, &queue_lock);
            }
            
            if(shutdown || queue_closed) 
            {
                pthread_mutex_unlock(&queue_lock);
                return 0;
            }
            
            /* fill in work structure */
            tpool_work<work_t,threadInfo> *workp = &queue[queue_head];

            workp->routine = routine;
            workp->arg = arg;

            /* advance queue head to next position */
            queue_head = (queue_head + 1) % max_queue_size;

            /* record keeping */
            cur_queue_size++;
            work_queued++;
            if(1 == cur_queue_size)
            {
                pthread_cond_broadcast(&queue_not_empty);
            }
            assert(cur_queue_size <= max_queue_size);
            
            pthread_mutex_unlock(&queue_lock);
            
            return 1;
        }

    void work(threadInfo *pInfo)
    {
        while(1)
        {
            pthread_mutex_lock(&queue_lock);
            total_work_done++;
            while( cur_queue_size == 0 && !(shutdown))
            {
		if(total_work_done == target_work_done)
		{
		    pthread_cond_signal(&queue_work_complete);
		}
                pthread_cond_wait(&queue_not_empty,&queue_lock);
            }
        
            if(shutdown)
            {
                pthread_mutex_unlock(&queue_lock);
                pthread_exit(NULL);
            }

            tpool_work<work_t,threadInfo> *my_workp = &queue[queue_tail];
            cur_queue_size--;

            assert(cur_queue_size >= 0);
            queue_tail = ( queue_tail + 1 ) % max_queue_size;

            if(cur_queue_size == max_queue_size - 1)
            {
                pthread_cond_broadcast(&queue_not_full);
            }

            if(0 == cur_queue_size)
            {
                pthread_cond_signal(&queue_empty);
            }

            void (*my_routine)(work_t&,threadInfo *) = my_workp->routine;
            /* NOT a work& reference because otherwise data could be
               overwritten before we can process it */
            work_t my_arg = my_workp->arg;
            pthread_mutex_unlock(&queue_lock);

            try
	    {
		/* actually do the work */
		((*my_routine))(my_arg, pInfo);
	    }
            catch(...)
	    {
		/* abort this task, but don't do anything else - 
		   main thread will notice soon */
	    }
        }
    }

    // block until all currently scheduled work is done
    void flush()
        {
            pthread_mutex_lock(&queue_lock);

            target_work_done = work_queued;

            // this signal in case all work already done
            pthread_cond_broadcast(&queue_not_empty); 

            while(total_work_done != target_work_done)
            {
                pthread_cond_wait(&queue_work_complete,&queue_lock);
            }

            target_work_done = INT_MAX;
            total_work_done = 0;
            work_queued=0;
            pthread_mutex_unlock(&queue_lock);
        }

    threadInfo* thread_info(int n)
        {
            return tinfo[n].info;
        }
 private:

    /* pool characteristics */
    int num_threads;
    int max_queue_size;
    tpool_threadInfo<threadInfo> *tinfo;
    
    /* pool state */
    pthread_t *threads;
    int cur_queue_size;
    int total_work_done;
    int work_queued;
    int target_work_done;

    int queue_head;
    int queue_tail;
    tpool_work<work_t,threadInfo> *queue;
    pthread_mutex_t queue_lock;
    pthread_cond_t queue_not_empty;
    pthread_cond_t queue_not_full;
    pthread_cond_t queue_empty;
    pthread_cond_t queue_work_complete;

    int queue_closed;
    int shutdown;


};

#endif /* _THREADPOOL_H_ */
