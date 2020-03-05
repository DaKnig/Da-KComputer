/*
  this is a prototype for the 3d shit in the DKC computer
  there are two sets of coordinates- screen and global coordinates.
  global coordinates are like in MC- y = up. in screen coordinates
  the standard coordinate system is used - x for horizontal, y for
  vertical, z for depth. camera at z=0; big z=> distant object.
*/

#include <stdio.h>
#include <SDL.h>
#include <inttypes.h>
#include <assert.h>
#include "putpixel.h"

#define FULLSCREEN 0

typedef Uint32 uint32;
typedef Uint16 uint16;
typedef Uint8  uint8;

typedef union Point {
    int32_t c[3];
    struct {
	int32_t x,y,z;
    };
} Point;
////	    putpixel(surface, x, y, pixel(0,127,0));
typedef struct Triangle {
    union Point p[3];
} Triangle;

#define swap(T,a,b) do{T temp__=a; a=b; b=temp__;} while(0)



int main(void) {
    assert(sizeof(Point) == sizeof (int32_t[3]));
    SDL_Init( SDL_INIT_EVERYTHING );

    SDL_Window* window =
	SDL_CreateWindow("prototype",200,200,640,480,
			 FULLSCREEN *SDL_WINDOW_FULLSCREEN);
    SDL_Surface* surface = SDL_GetWindowSurface( window );


/*
    for (int x=9; x<300; x++)
	for (int y=20; y<90; y++)
	    putpixel(surface, x, y, pixel(0,127,0));
*/



    int quit = 0;
    SDL_Event e;
    while(!quit) {
	while( SDL_PollEvent( &e ) != 0 ) {
	    switch (e.type) {
	    case SDL_QUIT:
		quit = 1;
	    }
	}
	SDL_UpdateWindowSurface( window );
    }

    {//totally kill SDL
	SDL_FreeSurface( surface );
	SDL_DestroyWindow( window );
	SDL_Quit();
    }
}
