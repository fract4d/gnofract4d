#include "fractFunc.h"
#include "pointFunc_public.h"
#include "fractWorker.h"
#include <stdio.h>
#include <stdlib.h>

IFractWorker *
IFractWorker::create(
    int nThreads,pf_obj *pfo, ColorMap *cmap, IImage *im_, IFractalSite *site)
{
// can IFDEF here if threads are not available
    if ( nThreads > 1)
    {
	return new MTFractWorker(nThreads,pfo,cmap,im_,site);
    }
    else
    {
	STFractWorker *w = new STFractWorker();
	if(!w) return w;
	w->init(pfo,cmap,im_,site);
	return w;
    }
} 

bool
STFractWorker::init(
    pf_obj *pfo, ColorMap *cmap, IImage *im_, IFractalSite *site)
{
    ff = NULL;
    im = im_;
    m_ok = true;

    pf = pointFunc::create(pfo,cmap,site);
    if(NULL == pf)
    {
	m_ok = false;
    }
    return m_ok;
}

STFractWorker::~STFractWorker()
{
    delete pf;
}

void
STFractWorker::set_fractFunc(fractFunc *ff_)
{
    ff = ff_;
}

/* we're in a worker thread */
void
STFractWorker::work(job_info_t& tdata)
{
    int nRows=0;

    int x = tdata.x;
    int y = tdata.y;
    int param = tdata.param;
    int param2 =  tdata.param2;
    job_type_t job = tdata.job;

    if(ff->try_finished_cond())
    {
        // interrupted - just return without doing anything
        // this is less efficient than clearing the queue but easier
        return;
    }

    /* carry them out */
    switch(job)
    {
    case JOB_BOX:
        //printf("BOX(%d,%d,%d) [%x]\n",x,y,param,(unsigned int)pthread_self());
        box(x,y,param);
        nRows = param;
        break;
    case JOB_ROW:
        //printf("ROW(%d,%d,%d) [%x]\n",x,y,param,(unsigned int)pthread_self());
        row(x,y,param);
        nRows=1;
        break;
    case JOB_BOX_ROW:
        //printf("BXR(%d,%d,%d) [%x]\n",x,y,param,(unsigned int)pthread_self());
        box_row(x, y, param);
        nRows = param;
        break;
    case JOB_ROW_AA:
        //printf("RAA(%d,%d,%d) [%x]\n",x,y,param,(unsigned int)pthread_self());
        row_aa(x,y,param);
        nRows=1;
        break;
    case JOB_QBOX_ROW:
        //printf("QBR(%d,%d,%d,%d) [%x]\n",x,y,param,param2,(unsigned int)pthread_self());
	qbox_row(x,y,param,param2);
	nRows = param;
	break;
    default:
        printf("Unknown job id %d ignored\n", (int) job);
    }
    ff->image_changed(0,y,im->Xres(),y+ nRows);
    ff->progress_changed((float)y/(float)im->Yres());
}

void
STFractWorker::row_aa(int x, int y, int w)
{
    for(int x = 0; x < w ; x++) {
        pixel_aa ( x, y);
    }
}

inline int
STFractWorker::periodGuess()
{ 
    if(!ff->periodicity)
    {
	return ff->maxiter;
    }
    if(lastIter == -1)
    {
	// we were captured last time so probably will be again
	return 0;
    }
    // we escaped, so don't try so hard this time
    return lastIter + 10;
}

inline int
STFractWorker::periodGuess(int x, int y)
{
    if (x <= 0)
    {
	return periodGuess();
    }
    fate_t previousxFate = im->getFate(x-1,y,0);
    if (FATE_UNKNOWN == previousxFate)
    {
	return periodGuess();
    }
    int last = im->getIter(x-1,y);
    return periodGuess(last);
}

inline int
STFractWorker::periodGuess(int last) {

    if(!ff->periodicity)
    {
	return ff->maxiter;
    }
    if(last == -1)
    {
	// we were captured last time so probably will be again
	return 0;
    }
    // we escaped, so don't try so hard this time
    return lastIter + 10;
}

inline void 
STFractWorker::periodSet(int *ppos) {
    lastIter = *ppos;
}

void
STFractWorker::row(int x, int y, int n)
{
    for(int i = 0; i < n; ++i)
    {
        pixel(x+i,y,1,1);
    }
}

void
STFractWorker::col(int x, int y, int n)
{
    for(int i = 0; i < n; ++i)
    {
        pixel(x,y+i,1,1);
    }
}

void
STFractWorker::reset_counts()
{
    stats.reset();
}

const pixel_stat_t&
STFractWorker::get_stats() const
{
    return stats;
}

inline int 
STFractWorker::RGB2INT(int x, int y)
{
    rgba_t pixel = im->get(x,y);
    return Pixel2INT(pixel);
}

inline int
STFractWorker::Pixel2INT(rgba_t pixel)
{
    int ret = (pixel.r << 16) | (pixel.g << 8) | pixel.b;
    return ret;
}

inline bool STFractWorker::isTheSame(
    bool bFlat, int targetIter, int targetCol, int x, int y)
{
    if (!bFlat) return false;
    // does this point have the target # of iterations?
    if(im->getIter(x,y) != targetIter) return false;
    // does it have the same colour too?
    if(RGB2INT(x,y) != targetCol) return false;
    return true;
}

rgba_t
STFractWorker::antialias(int x, int y)
{
    dvec4 topleft = ff->aa_topleft + x * ff->deltax + y * ff->deltay;

    dvec4 pos = topleft; 

    rgba_t ptmp, last;
    unsigned int pixel_r_val=0, pixel_g_val=0, pixel_b_val=0;    
    int p=0;
    float index;
    fate_t fate;

    int single_iters = im->getIter(x,y);
    int checkPeriod = periodGuess(single_iters); 

    if(ff->debug_flags & DEBUG_DRAWING_STATS)
    {
	printf("doaa %d %d\n", x, y);
    }

    last = im->get(x,y);
    // top left
    fate = im->getFate(x,y,0);
    if(im->hasUnknownSubpixels(x,y))
    {
	pf->calc(
	    pos.n, ff->maxiter,
	    checkPeriod, ff->period_tolerance, 
	    ff->warp_param,
	    x,y,1,
	    &ptmp,&p,&index,&fate); 
	im->setFate(x,y,0,fate);
	im->setIndex(x,y,0,index);
    }
    else
    {
	ptmp = pf->recolor(im->getIndex(x,y,0), fate, last);
    }

    pixel_r_val += ptmp.r;
    pixel_g_val += ptmp.g;
    pixel_b_val += ptmp.b;
	
    
    // top right
    fate = im->getFate(x,y,1);
    if(fate == FATE_UNKNOWN)
    {	
	pos+=ff->delta_aa_x;
	pf->calc(
	    pos.n, ff->maxiter,
	    checkPeriod, ff->period_tolerance,
	    ff->warp_param,
	    x,y,2,
	    &ptmp,&p,&index,&fate); 
	im->setFate(x,y,1,fate);
	im->setIndex(x,y,1,index);
    }
    else
    {
	ptmp = pf->recolor(im->getIndex(x,y,1), fate, last);
    }

    pixel_r_val += ptmp.r;
    pixel_g_val += ptmp.g;
    pixel_b_val += ptmp.b;

    // bottom left
    fate = im->getFate(x,y,2);
    if(fate == FATE_UNKNOWN)
    {	
	pos = topleft + ff->delta_aa_y;
	pf->calc(
	    pos.n, ff->maxiter,
	    checkPeriod,ff->period_tolerance,
	    ff->warp_param,
	    x,y,3,
	    &ptmp,&p,&index,&fate); 
	im->setFate(x,y,2,fate);
	im->setIndex(x,y,2,index);
    }
    else
    {
	ptmp = pf->recolor(im->getIndex(x,y,2), fate, last);
    }

    pixel_r_val += ptmp.r;
    pixel_g_val += ptmp.g;
    pixel_b_val += ptmp.b;

    // bottom right
    fate = im->getFate(x,y,3);
    if(fate == FATE_UNKNOWN)
    {	
	pos = topleft + ff->delta_aa_y + ff->delta_aa_x;
	pf->calc(
	    pos.n, ff->maxiter,
	    checkPeriod,ff->period_tolerance,
	    ff->warp_param,
	    x,y,4,
	    &ptmp,&p,&index,&fate); 
	im->setFate(x,y,3,fate);
	im->setIndex(x,y,3,index);
    }
    else
    {
	ptmp = pf->recolor(im->getIndex(x,y,3), fate, last);
    }

    pixel_r_val += ptmp.r;
    pixel_g_val += ptmp.g;
    pixel_b_val += ptmp.b;

    ptmp.r = pixel_r_val / 4;
    ptmp.g = pixel_g_val / 4;
    ptmp.b = pixel_b_val / 4;
    return ptmp;
}


void
STFractWorker::compute_stats(const dvec4& pos, int iter, fate_t fate, int x, int y)
{
    stats.s[ITERATIONS] += iter;
    stats.s[PIXELS]++;
    stats.s[PIXELS_CALCULATED]++;
    if (fate & FATE_INSIDE)
    {
	stats.s[PIXELS_INSIDE]++;
	if (iter < ff->maxiter-1)
	{
	    stats.s[PIXELS_PERIODIC]++;
	}
    }
    else
    {
	stats.s[PIXELS_OUTSIDE]++;
    }

    if (ff->auto_deepen && stats.s[PIXELS] % ff->AUTO_DEEPEN_FREQUENCY == 0)
    {
	compute_auto_deepen_stats(pos, iter, x, y);
    }
    if (ff->periodicity && ff->auto_tolerance && 
	stats.s[PIXELS] % ff->AUTO_TOLERANCE_FREQUENCY == 0)
    {
	compute_auto_tolerance_stats(pos, iter, x, y);
    }
}

void
STFractWorker::compute_auto_tolerance_stats(const dvec4& pos, int iter, int x, int y)
{
    if(iter == -1)
    {
	// currently inside
	
	// Possibly we incorrectly classified this as inside due to
	// loose period tolerance. Try with a tighter bound and see if it helps
	rgba_t temp_pixel;
	float temp_index;
	fate_t temp_fate;
	int temp_iter;
	/* try again with 10x tighter tolerance */
	pf->calc(
	    pos.n, ff->maxiter,
	    0, ff->period_tolerance / 10.0,
	    ff->warp_param,
	    x,y,-1,
	    &temp_pixel,&temp_iter, &temp_index, &temp_fate);
	    
	if(temp_iter != -1)
	{
	    // current tolerance is too loose, we would get 1 more
	    // pixel correct if we tightened it
	    stats.s[BETTER_TOLERANCE_PIXELS]++;
	}
    }
    else
    {
	// currently outside
	
	// Possibly we're trying too hard, and we'd still get this right with a 
	// looser period tolerance. Try it and see
	rgba_t temp_pixel;
	float temp_index;
	fate_t temp_fate;
	int temp_iter;
	/* try again with 10x looser tolerance */
	pf->calc(
	    pos.n, ff->maxiter,
	    0, ff->period_tolerance * 10.0,
	    ff->warp_param,
	    x,y,-1,
	    &temp_pixel,&temp_iter, &temp_index, &temp_fate);
	    
	if(temp_iter == -1)
	{
	    // if we loosened, we'd get this pixel wrong
	    stats.s[WORSE_TOLERANCE_PIXELS]++;
	}
    }
}

void
STFractWorker::compute_auto_deepen_stats(const dvec4& pos, int iter, int x, int y)
{
    if( iter > ff->maxiter/2)
    {
	/* we would have got this wrong if we used 
	 * half as many iterations */
	stats.s[WORSE_DEPTH_PIXELS]++;
    }
    else if(iter == -1)
    {
	rgba_t temp_pixel;
	float temp_index;
	fate_t temp_fate;
	int temp_iter;
	/* didn't bail out, try again with 2x as many iterations */
	pf->calc(
	    pos.n, ff->maxiter*2,
	    periodGuess(), ff->period_tolerance,
	    ff->warp_param,
	    x,y,-1,
	    &temp_pixel,&temp_iter, &temp_index, &temp_fate);
	    
	if(temp_iter != -1)
	{
	    /* we would have got this right if we used
	     * twice as many iterations */
	    stats.s[BETTER_DEPTH_PIXELS]++;
	}
    }
}

void 
STFractWorker::pixel(int x, int y,int w, int h)
{
    assert(pf != NULL && m_ok == true);

    rgba_t pixel;
    float index;

    fate_t fate = im->getFate(x,y,0);

    if(fate == FATE_UNKNOWN)
    {
	int iter = 0;
	
	switch(ff->render_type)
	{
	case RENDER_TWO_D: 
	{
	    // calculate coords of this point
	    dvec4 pos = ff->topleft + x * ff->deltax + y * ff->deltay;

	    //printf("(%d,%d -> %g,%g,%g,%g) [%x]\n",
	    //	   x,y,pos[VX],pos[VY],pos[VZ],pos[VW], (unsigned int)pthread_self());
	    
	    pf->calc(
		pos.n, ff->maxiter,
		periodGuess(), ff->period_tolerance,
		ff->warp_param,
		x,y,0,
		&pixel,&iter,&index,&fate);

	    compute_stats(pos,iter,fate,x,y);
	}
	break;
	case RENDER_LANDSCAPE:
	    assert(0 && "not supported");
	    break;

	case RENDER_THREE_D:
	{
	    dvec4 look = ff->vec_for_point(x,y);
	    dvec4 root;
	    bool found = find_root(ff->eye_point, look, root);
	    if(found)
	    {
		// intersected
		iter = -1;
		pixel.r = pixel.g = pixel.b = 0;
		fate = 1;
		index = 0.0;
	    }
	    else
	    {
		// did not intersect
		iter = 1;
		pixel.r = pixel.g = pixel.b = 0xff;
		fate = 0;
		index = 1.0;
	    }
	}
	    break;
	}

	periodSet(&iter);

	if(ff->debug_flags & DEBUG_DRAWING_STATS)
	{
	    printf("pixel %d %d %d %d\n", x, y, fate, iter);
	}

	assert(fate != FATE_UNKNOWN);
	im->setIter(x,y,iter);
	im->setFate(x,y,0,fate);
	im->setIndex(x,y,0,index);

	rectangle(pixel,x,y,w,h);
    }
    else
    {
	pixel = pf->recolor(im->getIndex(x,y,0), fate, im->get(x,y));
	rectangle(pixel,x,y,w,h);
    }
}

void 
STFractWorker::box_row(int w, int y, int rsize)
{
    // we increment by rsize-1 because we want to reuse the vertical bars
    // between the boxes - each box overlaps by 1 pixel
    int x;
    for(x = 0; x < w - rsize ; x += rsize -1) {
        box(x,y,rsize);            
    }		
    // extra pixels at end of lines
    for(int y2 = y; y2 < y + rsize; ++y2)
    {
	row (x, y2, w-x);
    }
}

void
STFractWorker::qbox_row(int w, int y, int rsize, int drawsize)
{
    int x;
    // main large blocks 
    for (x = 0 ; x< w - rsize ; x += rsize -1) 
    {
	pixel ( x, y, drawsize, drawsize);
    }
    // extra pixels at end of lines
    for(int y2 = y; y2 < y + rsize; ++y2)
    {
	row (x, y2, w-x);
    }
}

bool
STFractWorker::needs_aa_calc(int x, int y)
{
    for(int i = 0; i < im->getNSubPixels(); ++i)
    {
	if(im->getFate(x,y,i) == FATE_UNKNOWN)
	{
	    return true;
	}
    }
    return false;
}

void
STFractWorker::pixel_aa(int x, int y)
{
    rgba_t pixel;

    int iter = im->getIter(x,y);

    
    // if aa type is fast, short-circuit some points
    if(ff->eaa == AA_FAST &&
       x > 0 && x < im->Xres()-1 && y > 0 && y < im->Yres()-1)
    {
        // check to see if this point is surrounded by others of the same colour
        // if so, don't bother recalculating
        int pcol = RGB2INT(x,y);
        bool bFlat = true;

        // this could go a lot faster if we cached some of this info
        //bFlat = isTheSame(bFlat,iter,pcol,x-1,y-1);
        bFlat = isTheSame(bFlat,iter,pcol,x,y-1);
        //bFlat = isTheSame(bFlat,iter,pcol,x+1,y-1);
        bFlat = isTheSame(bFlat,iter,pcol,x-1,y);
        bFlat = isTheSame(bFlat,iter,pcol,x+1,y);
        //bFlat = isTheSame(bFlat,iter,pcol,x-1,y+1);
        bFlat = isTheSame(bFlat,iter,pcol,x,y+1);
        //bFlat = isTheSame(bFlat,iter,pcol,x+1,y+1);
        if(bFlat) 	    
        {
	    if(ff->debug_flags & DEBUG_DRAWING_STATS)
	    {
		printf("noaa %d %d\n", x, y);
	    }
	    im->fill_subpixels(x,y);
            return;
        }
    }

    pixel = antialias(x,y);

    rectangle(pixel,x,y,1,1,true);
}

bool 
STFractWorker::isNearlyFlat(int x, int y, int rsize)
{
    rgba_t colors[2];
    fate_t fate = im->getFate(x,y,0);

    const int MAXERROR=3;

    // can we predict the top edge close enough?
    colors[0] = im->get(x,y); // topleft
    colors[1] = im->get(x+rsize-1,y); //topright
    int x2;

    for (x2 = x+1; x2 < x+rsize-1; ++x2)
    {
	if (im->getFate(x2,y,0) != fate) return false;

	rgba_t predicted = predict_color(colors,(double)(x2-x)/rsize);
	int diff = diff_colors(predicted, im->get(x2,y));
	if (diff > MAXERROR)
	{
	    return false;
	}
    }

    // how about the bottom edge?
    int y2 = y + rsize -1;
    colors[0] = im->get(x,y2); // botleft
    colors[1] = im->get(x+rsize-1,y2); // botright

    for (x2 = x+1; x2 < x+rsize-1; ++x2)
    {
	if (im->getFate(x2,y2,0) != fate) return false;

	rgba_t predicted = predict_color(colors,(double)(x2-x)/rsize);
	int diff = diff_colors(predicted, im->get(x2,y2));
	if (diff > MAXERROR)
	{
	    return false;
	}
    }

    // how about the left side?
    colors[0] = im->get(x,y); 
    colors[1] = im->get(x,y+rsize-1); 

    for (y2 = y+1; y2 < y+rsize-1; ++y2)
    {
	if (im->getFate(x,y2,0) != fate) return false;

	rgba_t predicted = predict_color(colors,(double)(y2-y)/rsize);
	int diff = diff_colors(predicted, im->get(x,y2));
	if (diff > MAXERROR)
	{
	    return false;
	}
    }

    // and finally the right
    x2 = x + rsize-1;
    colors[0] = im->get(x2,y); 
    colors[1] = im->get(x2,y+rsize-1); 

    for (y2 = y+1; y2 < y+rsize-1; ++y2)
    {
	if (im->getFate(x2,y2,0) != fate) return false;

	rgba_t predicted = predict_color(colors,(double)(y2-y)/rsize);
	int diff = diff_colors(predicted, im->get(x2,y2));
	if (diff > MAXERROR)
	{
	    return false;
	}
    }

    return true;
}

// linearly interpolate over a rectangle
void
STFractWorker::interpolate_rectangle(int x, int y, int rsize)
{
    for (int y2 = y ; y2 < y+rsize-1; ++y2)
    {
	interpolate_row(x,y2,rsize);
    }
}

void
STFractWorker::interpolate_row(int x, int y, int rsize)
{
    fate_t fate = im->getFate(x,y,0);
    rgba_t colors[2];
    colors[0] = im->get(x,y); // left
    colors[1] = im->get(x+rsize-1,y); //right
    int iters[2];
    iters[0] = im->getIter(x,y);
    iters[1] = im->getIter(x+rsize-1,y);

    int indexes[2];
    indexes[0] = im->getIndex(x,y,0);
    indexes[1] = im->getIndex(x+rsize-1,y,0);
    
    for (int x2 =x ; x2 < x+rsize-1; ++x2)
    {
	double factor = (double)(x2-x)/rsize;
	rgba_t predicted_color = predict_color(colors, factor);
	int predicted_iter = predict_iter(iters, factor);
	float predicted_index = predict_index(indexes, factor);

	//check_guess(x2,y,predicted_color,fate,predicted_iter,predicted_index);
	im->put(x2,y,predicted_color);	
	im->setIter(x2,y,predicted_iter);
	im->setFate(x2,y,0,fate);
	im->setIndex(x2,y,0,predicted_index);
	stats.s[PIXELS]++;
	stats.s[PIXELS_SKIPPED]++;
    }
}

// linearly interpolate between colors to guess correct color
rgba_t
STFractWorker::predict_color(rgba_t colors[2], double factor)
{
    rgba_t result;
    result.r = (int)(colors[0].r * (1.0 - factor) + colors[1].r * factor);
    result.g = (int)(colors[0].g * (1.0 - factor) + colors[1].g * factor);
    result.b = (int)(colors[0].b * (1.0 - factor) + colors[1].b * factor);
    result.a = (int)(colors[0].a * (1.0 - factor) + colors[1].a * factor);
    return result;
}

int
STFractWorker::predict_iter(int iters[2], double factor)
{
    return (int)(iters[0] * (1.0 - factor) + iters[1] * factor);
}

float
STFractWorker::predict_index(int indexes[2], double factor)
{
    return (indexes[0] * (1.0 - factor) + indexes[1] * factor);
}


// sum squared differences between components of 2 colors
int
STFractWorker::diff_colors(rgba_t a, rgba_t b)
{
    int dr = a.r - b.r;
    int dg = a.g - b.g;
    int db = a.b - b.b;
    int da = a.a - b.a;

    return dr*dr + dg*dg + db*db + da*da;
}

void 
STFractWorker::box(int x, int y, int rsize)
{
    // calculate edges of box to see if they're all the same colour
    // if they are, we assume that the box is a solid colour and
    // don't calculate the interior points
    bool bFlat = true;
    int iter = im->getIter(x,y);
    int pcol = RGB2INT(x,y);
    
    // calculate top and bottom of box & check for flatness
    for(int x2 = x; x2 < x + rsize; ++x2)
    {
        pixel(x2,y,1,1);
        bFlat = isTheSame(bFlat,iter,pcol,x2,y);
        pixel(x2,y+rsize-1,1,1);        
        bFlat = isTheSame(bFlat,iter,pcol,x2,y+rsize-1);
    }
    // calc left and right of box & check for flatness
    for(int y2 = y; y2 < y + rsize; ++y2)
    {
        pixel(x,y2,1,1);
        bFlat = isTheSame(bFlat, iter, pcol, x, y2);
        pixel(x+rsize-1,y2,1,1);
        bFlat = isTheSame(bFlat,iter,pcol,x+rsize-1,y2);
    }
    
    if(bFlat)
    {
        // just draw a solid rectangle
        rgba_t pixel = im->get(x,y);
	fate_t fate = im->getFate(x,y,0);
	float index = im->getIndex(x,y,0);
        rectangle_with_iter(pixel,fate,iter,index,x+1,y+1,rsize-2,rsize-2);
    }
    else
    {
	bool nearlyFlat = false && isNearlyFlat(x,y,rsize);
	if (nearlyFlat)
	{
	    //printf("nf: %d %d %d\n", x, y, rsize);
	    interpolate_rectangle(x,y,rsize);
	}
	else
	{
	    //printf("bumpy: %d %d %d\n", x, y, rsize);

	    if(rsize > 4)
	    {	    
		// divide into 4 sub-boxes and check those for flatness
		int half_size = rsize/2;
		box(x,y,half_size);
		box(x+half_size,y,half_size);
		box(x,y+half_size, half_size);
		box(x+half_size,y+half_size, half_size);
	    }
	    else
	    {
		// we do need to calculate the interior 
		// points individually
		for(int y2 = y + 1 ; y2 < y + rsize -1; ++y2)
		{
		    row(x+1,y2,rsize-2);
		}
	    }
	}
    }		
}

inline void
STFractWorker::rectangle(
    rgba_t pixel, int x, int y, int w, int h, bool force)
{
    for(int i = y ; i < y+h; i++)
    {
        for(int j = x; j < x+w; j++) 
	{
	    im->put(j,i,pixel);
	}
    }
}

inline void
STFractWorker::check_guess(int x, int y, rgba_t pixel, fate_t fate, int iter, float index)
{
    // check if guess was correct
    if (true) 
    {
	dvec4 pos = ff->topleft + x * ff->deltax + y * ff->deltay;
	rgba_t tpixel;
	int titer;
	float tindex;
	fate_t tfate;
	pf->calc(
	    pos.n, ff->maxiter,
	    periodGuess(), ff->period_tolerance,
	    ff->warp_param,
	    x,y,0,
	    &tpixel,&titer,&tindex,&tfate);
	if (Pixel2INT(tpixel) == Pixel2INT(pixel))
//	    fate == tfate &&
//	    iter == titer &&
//	    fabs(index-tindex) < 1.0e-2)
	{
	    stats.s[PIXELS_SKIPPED_RIGHT]++;
	}
	else
	{
	    stats.s[PIXELS_SKIPPED_WRONG]++;
	}
    }

}

inline void
STFractWorker::rectangle_with_iter(
    rgba_t pixel, fate_t fate, int iter, float index, 
    int x, int y, int w, int h)
{
    for(int i = y ; i < y+h; i++)
    {
        for(int j = x; j < x+w; j++) 
	{
	    if(ff->debug_flags & DEBUG_DRAWING_STATS)
	    {
		printf("guess %d %d %d %d\n",j,i,fate,iter);
	    }
	    
	    //check_guess(j,i,pixel,fate,iter,index);
            im->put(j,i,pixel);
            im->setIter(j,i,iter);
	    im->setFate(j,i,0,fate);
	    im->setIndex(j,i,0,index);
	    stats.s[PIXELS]++;
	    stats.s[PIXELS_SKIPPED]++;
        }
    }
}


bool
STFractWorker::find_root(const dvec4& eye, const dvec4& look, dvec4& root)
{
    d dist = 0.0;

    rgba_t pixel;
    float index;
    fate_t fate = FATE_UNKNOWN;
    int iter;
    int x=-1, y=-1;

    int steps = 0;
    d lastdist = dist;
    dvec4 pos;

    while(1)
    {
	if(dist > 1.0e3) // FIXME
	{
	    // couldn't find anything
#ifdef DEBUG_ROOTS
	    printf("not found after %d\n", steps);
#endif
	    return false;
 	}

	pos = eye + dist * look;
    
	//printf("%g %g %g %g\n", pos[0], pos[1], pos[2], pos[3]);
	pf->calc(
	    pos.n, ff->maxiter,
	    periodGuess(), ff->period_tolerance,
	    ff->warp_param,
	    x,y,0,
	    &pixel,&iter,&index,&fate); 
    
	steps += 1;
	if(fate != 0) // FIXME
	{
	    // inside
#ifdef DEBUG_ROOTS
	    printf("bracketed after %d\n", steps);
#endif
	    break;
	}

	lastdist = dist;
	dist += 0.1;
    }

    // the root must be between lastdist and dist
    // bisect a few times to polish the root

    while(fabs(lastdist - dist) > 1.0E-10) // FIXME
    {
	d mid = (lastdist + dist)/2.0;

	pos = eye + mid * look;
	pf->calc(pos.n, ff->maxiter,
		 periodGuess(), ff->period_tolerance,
		 ff->warp_param,
		 x,y,0,
		 &pixel,&iter,&index,&fate); 

	if( fate != 0) // FIXME
	{
	    //inside, root must be further out
	    dist = mid;
	}
	else
	{
	    //outside, root must be further in
	    lastdist = mid;
	}
	steps += 1;
    }
#ifdef DEBUG_ROOTS
    printf("polished after %d\n", steps);
#endif
    root = pos;
    return true;
}
