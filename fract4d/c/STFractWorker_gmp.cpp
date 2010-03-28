#include "fractFunc.h"
#include "pointFunc_public.h"
#include "fractWorker.h"
#include <stdio.h>

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
        //cout << "BOX " << y << " " << pthread_self() << "\n";
        box(x,y,param);
        nRows = param;
        break;
    case JOB_ROW:
        //cout << "ROW " << y << " " << pthread_self() << "\n";
        row(x,y,param);
        nRows=1;
        break;
    case JOB_BOX_ROW:
        //cout << "BXR " << y << " " << pthread_self() << "\n";
        box_row(x, y, param);
        nRows = param;
        break;
    case JOB_ROW_AA:
        //cout << "RAA " << y << " " << pthread_self() << "\n";
        row_aa(x,y,param);
        nRows=1;
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

inline bool 
STFractWorker::periodGuess()
{ 
    return (ff->periodicity && lastIter == -1 && ff->maxiter > 4096);
}

inline bool 
STFractWorker::periodGuess(int last) {
    return ff->periodicity && last == -1;
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
STFractWorker::reset_counts()
{
    ndoubleiters=0;
    nhalfiters=0;
    k=0;
}

void 
STFractWorker::stats(int *pnDoubleIters, int *pnHalfIters, int *pk)
{
    *pnDoubleIters = ndoubleiters;
    *pnHalfIters = nhalfiters;
    *pk = k;
}

inline int 
STFractWorker::RGB2INT(int x, int y)
{
    rgba_t pixel = im->get(x,y);
    int ret = (pixel.r << 16) | (pixel.g << 8) | pixel.b;
    return ret;
}

inline bool STFractWorker::isTheSame(
    bool bFlat, int targetIter, int targetCol, int x, int y)
{
    if(bFlat)
    {
        // does this point have the target # of iterations?
        if(im->getIter(x,y) != targetIter) return false;
        // does it have the same colour too?
        if(RGB2INT(x,y) != targetCol) return false;
	// other point is unknown
	//if(im->getFate(x,y,0) & FATE_UNKNOWN) return false;
    }
    return bFlat;
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
    bool checkPeriod = periodGuess(single_iters); 

    if(ff->debug_flags & DEBUG_DRAWING_STATS)
    {
	printf("doaa %d %d\n", x, y);
    }

    last = im->get(x,y);
    // top left
    fate = im->getFate(x,y,0);
    if(im->hasUnknownSubpixels(x,y))
    {
	pf->calc(pos.n, ff->maxiter,checkPeriod,ff->warp_param,x,y,1,&ptmp,&p,&index,&fate); 
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
	pf->calc(pos.n, ff->maxiter,checkPeriod,ff->warp_param,x,y,2,&ptmp,&p,&index,&fate); 
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
	pf->calc(pos.n, ff->maxiter,checkPeriod,ff->warp_param,x,y,3,&ptmp,&p,&index,&fate); 
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
	pf->calc(pos.n, ff->maxiter,checkPeriod,ff->warp_param,x,y,4,&ptmp,&p,&index,&fate); 
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

	    //printf("(%g,%g,%g,%g)\n",pos[VX],pos[VY],pos[VZ],pos[VW]);

	    pf->calc(pos.n, ff->maxiter,periodGuess(),ff->warp_param,
		     x,y,0,
		     &pixel,&iter,&index,&fate);

	    // test for iteration depth
	    if(ff->auto_deepen && k++ % ff->AUTO_DEEPEN_FREQUENCY == 0)
	    {
		if( iter > ff->maxiter/2)
		{
		    /* we would have got this wrong if we used 
		     * half as many iterations */
		    nhalfiters++;
		}
		else if(iter == -1)
		{
		    rgba_t temp_pixel;
		    float temp_index;
		    fate_t temp_fate;
		    int temp_iter;
		    /* didn't bail out, try again with 2x as many iterations */
		    pf->calc(pos.n, ff->maxiter*2,periodGuess(),ff->warp_param,
			     x,y,-1,
			     &temp_pixel,&temp_iter, &temp_index, &temp_fate);
		    
		    if(temp_iter != -1)
		    {
			/* we would have got this right if we used
			 * twice as many iterations */
			ndoubleiters++;
		    }
		}
	    }
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
    for(int x = 0; x < w - rsize ; x += rsize) {
        box(x,y,rsize);            
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
        bFlat = isTheSame(bFlat,iter,pcol,x-1,y-1);
        bFlat = isTheSame(bFlat,iter,pcol,x,y-1);
        bFlat = isTheSame(bFlat,iter,pcol,x+1,y-1);
        bFlat = isTheSame(bFlat,iter,pcol,x-1,y);
        bFlat = isTheSame(bFlat,iter,pcol,x+1,y);
        bFlat = isTheSame(bFlat,iter,pcol,x-1,y+1);
        bFlat = isTheSame(bFlat,iter,pcol,x,y+1);
        bFlat = isTheSame(bFlat,iter,pcol,x+1,y+1);
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
    for(int y2 = y; y2 <= y + rsize; ++y2)
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
            im->put(j,i,pixel);
            im->setIter(j,i,iter);
	    im->setFate(j,i,0,fate);
	    im->setIndex(j,i,0,index);
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
	pf->calc(pos.n, ff->maxiter,periodGuess(),ff->warp_param,
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
	pf->calc(pos.n, ff->maxiter,periodGuess(),ff->warp_param,
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
