#include "fractWorker.h" 
#include "fractFunc.h"

/* redirect back to a member function */
void worker(job_info_t& tdata, STFractWorker *pFunc)
{
    pFunc->work(tdata);
}

MTFractWorker::MTFractWorker(
    int n, 
    pf_obj *pfo,
    ColorMap *cmap,
    IImage *im,
    IFractalSite *site)
{
    m_ok = true;
    /* 0'th ftf is in this thread for calculations we don't want to offload */
    nWorkers = n > 1 ? n + 1 : 1;

    ptf = new STFractWorker[nWorkers];
    for(int i = 0; i < nWorkers; ++i)
    {
        if(!ptf[i].init(pfo,cmap,im,site))
        {
            // failed to create - mark this dead 
            m_ok = false;	    
        }
    }

    if(n > 1)
    {
        ptp = new tpool<job_info_t,STFractWorker>(n,100,ptf);
    }
    else
    {
        ptp = NULL;
    }
}

MTFractWorker::~MTFractWorker()
{
    delete ptp;
    delete[] ptf;
}

void
MTFractWorker::set_fractFunc(fractFunc *ff_)
{
    for(int i = 0; i < nWorkers; ++i)
    {
	ptf[i].set_fractFunc(ff_);
    }
}

void
MTFractWorker::row_aa(int x, int y, int n)
{
    if(nWorkers > 1 && n > 8)
    {
	send_row_aa(x,y,n);
    }
    else
    {
	ptf->row_aa(x,y,n);
    }
}

void
MTFractWorker::row(int x, int y, int n)
{
    if(nWorkers > 1 && n > 8)
    {
	send_row(x,y,n);
    }
    else
    {
	ptf->row(x,y,n);
    }
}

void
MTFractWorker::box(int x, int y, int rsize)
{
    ptf->box(x,y,rsize);
}

void
MTFractWorker::box_row(int w, int y, int rsize)
{
    if(nWorkers > 1)
    {
	send_box_row(w,y,rsize);
    }
    else
    {
	ptf->box_row(w,y,rsize);
    }
}

void
MTFractWorker::pixel(int x, int y, int w, int h)
{
    ptf->pixel(x,y,w,h);
}

void
MTFractWorker::pixel_aa(int x, int y)
{

}

void
MTFractWorker::reset_counts()
{
    for(int i = 0; i < nWorkers ; ++i)
    {
        ptf[i].reset_counts();
    }
}

void
MTFractWorker::stats(int *pnDoubleIters, int *pnHalfIters, int *pk)
{ 
    *pnDoubleIters = 0;
    *pnHalfIters = 0;
    *pk = 0;
    for(int i = 0; i < nWorkers; ++i)
    {
	int nd, nh, k;
	ptf[i].stats(&nd,&nh,&k);
        *pnDoubleIters += nd;
        *pnHalfIters += nh;
        *pk += k;
    }
}

void
MTFractWorker::send_cmd(job_type_t job, int x, int y, int param)
{
    job_info_t work;

    work.job = job; 
    work.x = x; work.y = y; work.param = param;

    ptp->add_work(worker, work);
}

void
MTFractWorker::send_row(int x, int y, int w)
{
    //cout << "sent ROW" << y << "\n";
    send_cmd(JOB_ROW,x,y,w);
}

void
MTFractWorker::send_box_row(int w, int y, int rsize)
{
    //cout << "sent BXR" << y << "\n";
    send_cmd(JOB_BOX_ROW, w, y, rsize);
}

void
MTFractWorker::send_box(int x, int y, int rsize)
{
    //cout << "sent BOX" << y << "\n";
    send_cmd(JOB_BOX,x,y,rsize);
}

void
MTFractWorker::send_row_aa(int x, int y, int w)
{
    //cout << "sent RAA" << y << "\n";
    send_cmd(JOB_ROW_AA, x, y, w);
}

void 
MTFractWorker::flush()
{
    if(ptp)
    {
        ptp->flush();
    }
}

bool
MTFractWorker::ok()
{ 
    return m_ok;
}

bool
MTFractWorker::find_root(const dvec4& eye, const dvec4& look, dvec4& root)
{
    return ptf->find_root(eye,look,root);
}
