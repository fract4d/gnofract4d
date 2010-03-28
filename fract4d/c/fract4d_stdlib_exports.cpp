// The following is to make the setup system happy under Windows:
#ifndef PyMODINIT_FUNC
#define PyMODINIT_FUNC void
#endif

extern "C" PyMODINIT_FUNC initfract4d_stdlib()
{
	// Dummy routine that Python can call to get this library, but which doesn't do anything.
}

#pragma comment(linker, "/EXPORT:_fract_rand")
#pragma comment(linker, "/EXPORT:_arena_create")
#pragma comment(linker, "/EXPORT:_arena_clear")
#pragma comment(linker, "/EXPORT:_arena_delete")
#pragma comment(linker, "/EXPORT:_arena_alloc")
#pragma comment(linker, "/EXPORT:_array_get_int")
#pragma comment(linker, "/EXPORT:_array_get_double")
#pragma comment(linker, "/EXPORT:_array_set_int")
#pragma comment(linker, "/EXPORT:_array_set_double")
#pragma comment(linker, "/EXPORT:_alloc_array1D")
#pragma comment(linker, "/EXPORT:_alloc_array2D")
#pragma comment(linker, "/EXPORT:_alloc_array3D")
#pragma comment(linker, "/EXPORT:_alloc_array4D")
#pragma comment(linker, "/EXPORT:_read_int_array_1D")
#pragma comment(linker, "/EXPORT:_write_int_array_1D")
#pragma comment(linker, "/EXPORT:_read_int_array_2D")
#pragma comment(linker, "/EXPORT:_write_int_array_2D")
#pragma comment(linker, "/EXPORT:_read_float_array_1D")
#pragma comment(linker, "/EXPORT:_write_float_array_1D")
#pragma comment(linker, "/EXPORT:_read_float_array_2D")
#pragma comment(linker, "/EXPORT:_write_float_array_2D")

extern "C"
{
	void fract_rand(double *re, double *im);
	typedef struct s_arena *arena_t;
	arena_t arena_create(int page_size, int max_pages);
	void arena_clear(arena_t arena);
	void arena_delete(arena_t arena);
	void *arena_alloc(arena_t arena, int element_size, int n_dimensions, int *n_elements);
	void array_get_int(void *allocation, int n_dimensions, int *indexes, int *pRetVal, int *pInBounds);
	void array_get_double(void *allocation, int n_dimensions, int *indexes, double *pRetVal, int *pInBounds);
	int array_set_int(void *allocation, int n_dimensions, int *indexes, int val);
	int array_set_double(void *allocation, int n_dimensions, int *indexes, double val);
	void *alloc_array1D(arena_t arena, int element_size, int size);
	void *alloc_array2D(arena_t arena, int element_size, int xsize, int ysize);
	void *alloc_array3D(arena_t arena, int element_size, int xsize, int ysize, int zsize);
	void *alloc_array4D(arena_t arena, int element_size, int xsize, int ysize, int zsize, int wsize);
	int read_int_array_1D(void *array, int x);
	int write_int_array_1D(void *array, int x, int val);
	int read_int_array_2D(void *array, int x, int y);
	int write_int_array_2D(void *array, int x, int y, int val);
	double read_float_array_1D(void *array, int x);
	int write_float_array_1D(void *array, int x, double val);
	double read_float_array_2D(void *array, int x, int y);
	int write_float_array_2D(void *array, int x, int y, double val);
}