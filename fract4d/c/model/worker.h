#ifndef __WORKER_H_INCLUDED__
#define __WORKER_H_INCLUDED__

#include <memory>
#include <vector>

#include "model/vectors.h"
#include "model/stats.h"
#include "model/pointfunc.h"
#include "model/threadpool.h"

class fractFunc;
class ColorMap;
class IImage;
class IFractalSite;
struct calc_options;
typedef struct s_rgba rgba_t;
typedef unsigned char fate_t;
typedef struct s_pf_data pf_obj;

/* enum for jobs */
typedef enum
{
    JOB_NONE,
    JOB_BOX,
    JOB_BOX_ROW,
    JOB_ROW,
    JOB_ROW_AA,
    JOB_QBOX_ROW
} job_type_t;

/* one unit of work */
typedef struct
{
    job_type_t job;
    int x, y, param, param2;
} job_info_t;

class STFractWorker;
void worker(job_info_t &tdata, STFractWorker *pFunc);

class IFractWorker
{
public:
    static IFractWorker *create(
        int numThreads, pf_obj *, ColorMap *, IImage *, IFractalSite *);

    virtual void set_fractFunc(fractFunc *) = 0;
    // calculate a row of antialiased pixels
    virtual void row_aa(int x, int y, int n) = 0;
    // calculate a row of pixels
    virtual void row(int x, int y, int n) = 0;
    // calculate an rsize-by-rsize box of pixels
    virtual void box(int x, int y, int rsize) = 0;
    // calculate a row of boxes
    virtual void box_row(int w, int y, int rsize) = 0;
    // calculate a row of boxes, quickly
    virtual void qbox_row(int w, int y, int rsize, int drawsize) = 0;
    // calculate a single pixel
    virtual void pixel(int x, int y, int w, int h) = 0;
    // calculate a single pixel in aa-mode
    virtual void pixel_aa(int x, int y) = 0;
    // auto-deepening record keeping
    virtual void reset_counts() = 0;
    virtual const pixel_stat_t &get_stats() const = 0;
    // ray-tracing machinery
    virtual bool find_root(const dvec4 &eye, const dvec4 &look, dvec4 &root) = 0;
    virtual void flush() = 0;

    virtual ~IFractWorker(){};
    bool ok() const { return m_ok; }
protected:
    bool m_ok = true;
    mutable pixel_stat_t m_stats;
};

/* per-worker-thread fractal info */
class STFractWorker final: public IFractWorker
{
public:
    STFractWorker(pf_obj *pfo, ColorMap *cmap, IImage *im, IFractalSite *site) noexcept:
        m_site{site}, m_im{im}, m_pf{pfo, cmap}, m_lastPointIters{0} { }

    // top-level function for multi-threaded workers
    void work(job_info_t &tdata);

    // IFractWorker interface
    void set_fractFunc(fractFunc *ff);
    void row_aa(int x, int y, int n);
    void row(int x, int y, int n);
    void box(int x, int y, int rsize);
    void box_row(int w, int y, int rsize);
    void qbox_row(int w, int y, int rsize, int drawsize);
    void pixel(int x, int y, int h, int w);
    void pixel_aa(int x, int y);
    void reset_counts();
    const pixel_stat_t &get_stats() const;
    bool find_root(const dvec4 &eye, const dvec4 &look, dvec4 &root);
    void flush(){};

private:
    void compute_stats(const dvec4 &pos, int iter, fate_t, int x, int y);
    void compute_auto_deepen_stats(const dvec4 &pos, int iter, int x, int y);
    void compute_auto_tolerance_stats(const dvec4 &pos, int iter, int x, int y);
    // return true if this pixel needs recalc in AA pass
    bool needs_aa_calc(int x, int y);
    // does the point at (x,y) have the same colour & iteration count as the target?
    bool isTheSame(int targetIter, int targetCol, int x, int y);
    // calculate this point using antialiasing
    rgba_t antialias(int x, int y);
    // make an int corresponding to an RGB triple
    int Pixel2INT(int x, int y);
    // heuristic to see if we should use periodicity checking for next point
    int periodGuess();
    // periodicity guesser for when we have the last count to hand
    // (as for antialias pass)
    int periodGuess(int last);
    // update whether last pixel bailed
    void periodSet(int *ppos);
    // draw a rectangle of this colour
    void rectangle(rgba_t, int x, int y, int w, int h, bool force = false);
    void rectangle_with_iter(rgba_t, fate_t, int iter, float index, int x, int y, int w, int h);

    // EXPERIMENTAL (not in use)
    // is the square with its top-left corner at (x,y) close-enough to flat
    // that we could interpolate & get a decent-looking image?
    bool isNearlyFlat(int x, int y, int rsize);
    // linearly interpolate between colors to guess correct color
    rgba_t predict_color(rgba_t colors[2], double factor);
    int predict_iter(int iters[2], double factor);
    float predict_index(int indexes[2], double factor);
    void interpolate_rectangle(int x, int y, int rsize);
    void interpolate_row(int x, int y, int rsize);
    // compare a prediction against the real answer & update stats
    void check_guess(int x, int y, rgba_t pixel, fate_t fate, int iter, float index);
    // periodicity guesser to look up nearby points & guess based on that
    int periodGuess(int x, int y);
    // calculate a column of pixels
    void col(int x, int y, int n);
    // sum squared differences between components of 2 colors
    int diff_colors(rgba_t a, rgba_t b);

    calc_options *m_options;
    IFractalSite *m_site;
    fractFunc *m_ff;
    /* pointers to data also held in fractFunc */
    IImage *m_im;
    // function object which calculates the colors of points
    // this is per-thread-func so it doesn't have to be re-entrant
    // and can have member vars
    pointFunc m_pf;
    // period guessing
    int m_lastPointIters; // how many iterations did last pixel take?
};

// a composite subclass which holds an array of STFractWorkers and
// divides the work among them
class MTFractWorker final: public IFractWorker
{
public:
    MTFractWorker(
        int numThreads,
        pf_obj *,
        ColorMap *,
        IImage *,
        IFractalSite *
    );

    // IFractWorker interface
    void set_fractFunc(fractFunc *ff);
    void row_aa(int x, int y, int n);
    void row(int x, int y, int n);
    void box(int x, int y, int rsize);
    void qbox_row(int w, int y, int rsize, int drawsize);
    void box_row(int w, int y, int rsize);
    void pixel(int x, int y, int h, int w);
    void pixel_aa(int x, int y);
    void reset_counts();
    const pixel_stat_t &get_stats() const;
    bool find_root(const dvec4 &eye, const dvec4 &look, dvec4 &root);
    void flush();

private:
    /* wait for a ready thread then give it some work */
    void send_cmd(job_type_t job, int x, int y, int param, int param2 = 0);
    void send_quit();
    void send_box(int x, int y, int rsize);
    void send_row(int x, int y, int n);
    void send_row_aa(int x, int y, int n);
    void send_box_row(int w, int y, int rsize);
    void send_qbox_row(int w, int y, int rsize, int drawsize);

    std::vector<STFractWorker> m_workers;
    std::unique_ptr<tpool<job_info_t, STFractWorker>> m_threads;
};

#endif