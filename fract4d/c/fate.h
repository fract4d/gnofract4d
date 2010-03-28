#ifndef FATE_H_
#define FATE_H_

/* the 'fate' of a point. This can be either
   Unknown (255) - not yet calculated
   N - reached an attractor numbered N (up to 30)
   N | FATE_INSIDE - did not escape
   N | FATE_SOLID - color with solid color 
   N | FATE_DIRECT - color with DCA
*/

typedef unsigned char fate_t;

#define FATE_UNKNOWN 255
#define FATE_SOLID 0x80
#define FATE_DIRECT 0x40
#define FATE_INSIDE 0x20

#endif /* COLOR_H_ */
