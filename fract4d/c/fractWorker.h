
#ifndef FRACT_WORKER_H_
#define FRACT_WORKER_H_

#include "fractWorker_public.h"
#include "pointFunc_public.h"

/* enum for jobs */
typedef enum {
    JOB_NONE,
    JOB_BOX,
    JOB_BOX_ROW,
    JOB_ROW,
    JOB_ROW_AA,
    JOB_QBOX_ROW
} job_type_t;

/* one unit of work */
typedef struct {
    job_type_t job;
    int x, y, param, param2;
} job_info_t;

/* per-worker-thread fractal info */
class STFractWorker : public IFractWorker {
 public:
    void set_fractFunc(fractFunc *ff); 

    /* pointers to data also held in fractFunc */
    IImage *im;    

    /* not a ctor because we always create a whole array then init them */
    bool init(pf_obj *pfo, ColorMap *cmap, IImage *im, IFractalSite *site);

    ~STFractWorker();    

    STFractWorker() {
	reset_counts();
        lastIter = 0;
    }

    // heuristic to see if we should use periodicity checking for next point
    inline int periodGuess();

    // periodicity guesser for when we have the last count to hand 
    // (as for antialias pass)
    inline int periodGuess(int last);

    // periodicity guesser to look up nearby points & guess based on that
    inline int periodGuess(int x, int y);

    // update whether last pixel bailed
    inline void periodSet(int *ppos);

    // top-level function for multi-threaded workers
    void work(job_info_t &tdata);

    // calculate a row of antialiased pixels
    void row_aa(int x, int y, int n);

    // calculate a row of pixels
    void row(int x, int y, int n);

    // calculate a column of pixels
    void col(int x, int y, int n);

    // calculate an rsize-by-rsize box of pixels
    void box(int x, int y, int rsize);

    // does the point at (x,y) have the same colour & iteration count
    // as the target?
    inline bool isTheSame(bool bFlat, int targetIter, int targetCol, int x, int y);

    // is the square with its top-left corner at (x,y) close-enough to flat
    // that we could interpolate & get a decent-looking image?
    bool isNearlyFlat(int x, int y, int rsize);

    // linearly interpolate between colors to guess correct color
    rgba_t predict_color(rgba_t colors[2], double factor);
    int predict_iter(int iters[2], double factor);
    float predict_index(int indexes[2], double factor);

    // sum squared differences between components of 2 colors
    int diff_colors(rgba_t a, rgba_t b);

    // make an int corresponding to an RGB triple
    inline int RGB2INT(int x, int y);
    inline int Pixel2INT(rgba_t pixel);

    // calculate a row of boxes
    void box_row(int w, int y, int rsize);

    // calculate a row of boxes, quickly
    void qbox_row(int w, int y, int rsize, int drawsize);

    // calculate a single pixel
    void pixel(int x, int y, int h, int w);

    // calculate a single pixel in aa-mode
    void pixel_aa(int x, int y);

    // draw a rectangle of this colour
    void rectangle(rgba_t pixel, 
		   int x, int y, int w, int h, 
		   bool force=false);

    void rectangle_with_iter(rgba_t pixel, fate_t fate, 
			     int iter, float index,
			     int x, int y, int w, int h);

    void interpolate_rectangle(int x, int y, int rsize);
    void interpolate_row(int x, int y, int rsize);

    // compare a prediction against the real answer & update stats
    inline void check_guess(int x, int y, rgba_t pixel, fate_t fate, int iter, float index);

    // calculate this point using antialiasing
    rgba_t antialias(int x, int y);

    void reset_counts();
    const pixel_stat_t& get_stats() const;

    void flush() {};
    bool ok() { return m_ok; }
 
    // ray-tracing machinery
    bool find_root(const dvec4& eye, const dvec4& look, dvec4& root);

 private:

    void compute_stats(const dvec4& pos, int iter, fate_t fate, int x, int y);
    void compute_auto_deepen_stats(const dvec4& pos, int iter, int x, int y);
    void compute_auto_tolerance_stats(const dvec4& pos, int iter, int x, int y);

    fractFunc *ff;

    // function object which calculates the colors of points 
    // this is per-thread-func so it doesn't have to be re-entrant
    // and can have member vars
    pointFunc *pf; 

    pixel_stat_t stats;

    // period guessing
    int lastIter; // how many iterations did last pixel take?


    // return true if this pixel needs recalc in AA pass
    bool needs_aa_calc(int x, int y);

    bool m_ok;
};

#include "threadpool.h"

void worker(job_info_t& tdata, STFractWorker *pFunc);

// a composite subclass which holds an array of STFractWorkers and
// divides the work among them
class MTFractWorker : public IFractWorker
{
 public:
    MTFractWorker(int n, 
		  pf_obj *obj,
		  ColorMap *cmap,
		  IImage *im,
		  IFractalSite *site);
    ~MTFractWorker();

    void set_fractFunc(fractFunc *ff); 

    // operations
    virtual void row_aa(int x, int y, int n) ;
    virtual void row(int x, int y, int n) ;
    virtual void box(int x, int y, int rsize) ;
    virtual void qbox_row(int w, int y, int rsize, int drawsize);
    virtual void box_row(int w, int y, int rsize);
    virtual void pixel(int x, int y, int h, int w);
    virtual void pixel_aa(int x, int y);

    // record keeping
    virtual void reset_counts();
    const pixel_stat_t& get_stats() const;

    virtual void flush();

    virtual bool ok();
    int nWorkers;

    bool find_root(const dvec4& eye, const dvec4& look, dvec4& root);

private:

    /* wait for a ready thread then give it some work */
    void send_cmd(job_type_t job, int x, int y, int param);
    void send_cmd(job_type_t job, int x, int y, int param, int param2);
    void send_quit();

    void send_box(int x, int y, int rsize);
    void send_row(int x, int y, int n);
    void send_row_aa(int x, int y, int n);
    void send_box_row(int w, int y, int rsize);
    void send_qbox_row(int w, int y, int rsize, int drawsize);

    STFractWorker *ptf;
    tpool<job_info_t,STFractWorker> *ptp;
    bool m_ok;
    mutable pixel_stat_t stats;
};

#endif /* FRACT_WORKER_H_ */
