
#ifndef __IMAGEUTILS_H_INCLUDED__
#define __IMAGEUTILS_H_INCLUDED__

/* functions called by compiled formulas */

#ifdef __cplusplus
extern "C" {
#endif

    void image_lookup(void *im, double x, double y, double *pr, double *pg, double *pb);

#ifdef __cplusplus
}
#endif

#endif /* __IMAGEUTILS_H_INCLUDED__ */
