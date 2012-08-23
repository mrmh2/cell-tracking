#include <excal3d2.h>
#include <ctype.h>

static TYPE **state;
static TYPE **state2;
static TYPE **state3;

static TYPE **tempstate;

static TYPE **modulation_x;
static TYPE **modulation_y;

static TYPE **modulation_x_man;
static TYPE **modulation_y_man;

static TYPE **modulation_x_west_i;
static TYPE **modulation_x_west_j;
static TYPE **modulation_x_east_i;
static TYPE **modulation_x_east_j;

static TYPE **modulation_y_south_i;
static TYPE **modulation_y_south_j;
static TYPE **modulation_y_north_i;
static TYPE **modulation_y_north_j;

static TYPE **modulation_x_web;
static TYPE **modulation_y_web;

static int ncol1,nrow1;
static int ncol2,nrow2;
static int complete;

static int currentx1,currenty1;
static int currentx2,currenty2;
static int linkedx,linkedy;

static double mod_x,mod_y;

extern int nrow,ncol,nlay;
extern int boundary;

extern void (*mouse)(int,int,int);
extern void (*keyboard)(int,int,int);

int RGB2Code(int r,int g,int b)
{
	r=max(0,min(255,r));
	g=max(0,min(255,g));
	b=max(0,min(255,b));
	return b+256*g+65536*r;
}

int Code2Color(int state, int which)
{
	int white,red,green,blue;
	
	blue=state%256;
	if(which==3) return blue;
	else {
		green=((state-blue)/256)%256;
		if(which==2)return green;
		else {
			red=(state-blue-256*green)/65536;
			if(which==1)return red;
			else {
				white=(int)((double)(red+green+blue)/3.);
				return white;
			}
		}
	}
}

int Color2Code(int intensity, int which)
{
	if(which==0) return intensity+256*intensity+65536*intensity;
	else if(which==1) return 65536*intensity;
	else if(which==2) return 256*intensity;
	else return intensity;
}

int MixColors(int color1, int color2, double opacity)
{
	int red1,green1,blue1;
	int red2,green2,blue2;
	int r,g,b;
	
	blue1=color1%256;
	green1=((color1-blue1)/256)%256;
	red1=(color1-blue1-256*green1)/65536;
	
	blue2=color2%256;
	green2=((color2-blue2)/256)%256;
	red2=(color2-blue2-256*green2)/65536;
	
	r=(int)((double)red1*(1.-opacity)+(double)red2*opacity);
	g=(int)((double)green1*(1.-opacity)+(double)green2*opacity);
	b=(int)((double)blue1*(1.-opacity)+(double)blue2*opacity);
	
	r=max(0,min(255,r));
	g=max(0,min(255,g));
	b=max(0,min(255,b));
	
	return b+256*g+65536*r;
}

void DisplayGraphics()
{
	int color1,color2;
	
	PLANE(tempstate[i][j]=state[i][j];);
	PLANE(
			if(i==currenty1 && j==currentx1) {
				NEIGHBOURS( 
							  if(!(i+y<1 || i+y>nrow || j+x<1 || j+x>ncol)) {
								  tempstate[i+y][j+x]=RGB2Code(0,255,0);
							  }
							  );
			}
			
			else if(i==linkedy && j==linkedx) {
				NEIGHBOURS( 
							  if(!(i+y<1 || i+y>nrow || j+x<1 || j+x>ncol)) {
								  tempstate[i+y][j+x]=RGB2Code(255,0,0);
							  }
							  );
			}
			);
	PlaneDisplay(tempstate,nrow,0,0); 
	
	PLANE(tempstate[i][j]=state2[i][j];);
	PLANE(
			if(i==currenty2 && j==currentx2) {
				NEIGHBOURS( 
							  if(!(i+y<1 || i+y>nrow || j+x<1 || j+x>ncol)) {
								  tempstate[i+y][j+x]=RGB2Code(0,255,0);
							  }
							  );
			}
			);
	PlaneDisplay(tempstate,nrow,ncol,0);
	PlaneDisplay(state3,0,0,0);
	
	PLANE(
			if(modulation_x_man[i][j]) {
				NEIGHBOURS( 
							  if(!(i+y<1 || i+y>nrow || j+x<1 || j+x>ncol)) {
								  tempstate[i+y][j+x]=RGB2Code(0,255,0);
							  }
							  );
			}
			
			else if(modulation_x_web[i][j]) {
				tempstate[i][j]=RGB2Code(255,255,0);
			}
			else if(modulation_y_web[i][j]) {
				tempstate[i][j]=RGB2Code(0,255,255);
			}
			else {
				tempstate[i][j]=0;
			}
			);
	PlaneDisplay(tempstate,0,ncol,0);
	
	PLANE(
			color1=rint(((double)modulation_x[i][j]/(double)ncol1)*255.);
			color2=rint(((double)modulation_y[i][j]/(double)nrow1)*255.);
			
			tempstate[i][j]=RGB2Code(color1,color2,255-color1);
			);
	
	PlaneDisplay(tempstate,0,2*ncol,0);
	
}

void LinkPoints()
{
	if(currentx1 && currenty1 && currentx2 && currenty2) {
		modulation_x_man[currenty2][currentx2]=currentx1;
		modulation_y_man[currenty2][currentx2]=currenty1;
		printf("Points linked (%d,%d) -> (%d->%d)\n", currentx1, currenty1, currentx2, currenty2);
	}
	
	else {
		printf("Select two points to link\n");
	}
}

void UpdateDirections()
{
	int x,y;
	double distance,mindistance,slope;
	
	int otheri,otherj;
	int mod,othermod;
	
	PLANE(
			modulation_x_web[i][j]=modulation_x_man[i][j];
			modulation_y_web[i][j]=modulation_y_man[i][j];
			);
	
	//find nearest neighbours for manual points
	PLANE(
			if(modulation_x_man[i][j]) {
				
				printf("Horizontally connecting fixed point for [%d][%d] -> %d\n",i,j,modulation_x_man[i][j]);
				
				//down
				if(i>1) {
					
					otherj=j;
					otheri=1;
					
					mod=modulation_x_man[i][j];
					othermod=modulation_x_man[i][j];
					
					mindistance=(double)(i-1);
					
					for(y=1;y<i;y++) {
						for(x=1;x<=ncol;x++) {
							
							if(abs(i-y)>=abs(j-x)) {
								
								if(modulation_x_man[y][x]) {
									distance=sqrt((double)((y-i)*(y-i))+(double)((x-j)*(x-j)));
									
									if(distance<mindistance) {
										otheri=y;
										otherj=x;
										mindistance=distance;
										othermod=modulation_x_man[y][x];
									}
								}
							}
						}
					}
					
					printf("\tConnecting to [%d][%d] -> %d\n",otheri,otherj,othermod);
					
					
					slope=(double)(j-otherj)/(i-otheri);
					
					//printf("\tSlope: %f\n",slope);
					
					for(y=otheri;y<i;y++) {
						
						x=rint((double)otherj+slope*(double)(y-otheri));
						distance=sqrt((double)((y-i)*(y-i))+(double)((x-j)*(x-j)));
						
						modulation_x_web[y][x]=rint(((double)mod*(mindistance-distance)+(double)othermod*distance)/mindistance);
						
						//printf("\tExtrapolation for [%d][%d] -> Distance: %f, Total distance: %f, Mod: %d, Othermod: %d, Modulation: %d\n",y,x,distance,mindistance,mod,othermod,modulation_x_web[y][x]);
					}
				}
				
				//up
				if(i<nrow) {
					
					otherj=j;
					otheri=nrow;
					
					mod=modulation_x_man[i][j];
					othermod=modulation_x_man[i][j];
					
					mindistance=(double)(nrow-1);
					
					for(y=i+1;y<=nrow;y++) {
						for(x=1;x<=ncol;x++) {
							
							if(abs(i-y)>=abs(j-x)) {
								
								if(modulation_x_man[y][x]) {
									distance=sqrt((double)((y-i)*(y-i))+(double)((x-j)*(x-j)));
									
									if(distance<mindistance) {
										otheri=y;
										otherj=x;
										mindistance=distance;
										othermod=modulation_x_man[y][x];
									}
								}
							}
						}
					}
					
					printf("\tConnecting to [%d][%d] -> %d\n",otheri,otherj,othermod);
					
					slope=(double)(otherj-j)/(otheri-i);
					
					//printf("\tSlope: %f\n",slope);
					
					for(y=i+1;y<=otheri;y++) {
						
						x=rint((double)j+slope*(double)(y-i));
						distance=sqrt((double)((y-i)*(y-i))+(double)((x-j)*(x-j)));
						
						modulation_x_web[y][x]=rint(((double)mod*(mindistance-distance)+(double)othermod*distance)/mindistance);
						
						//printf("\tExtrapolation for [%d][%d] -> Distance: %f, Total distance: %f, Mod: %d, Othermod: %d, Modulation: %d\n",y,x,distance,mindistance,mod,othermod,modulation_x_web[y][x]);
					}
				}
			}
			
			if(modulation_y_man[i][j]) {
								
				//left
				if(j>1) {
					
					otherj=1;
					otheri=i;
					
					mod=modulation_y_man[i][j];
					othermod=modulation_y_man[i][j];
					
					mindistance=(double)(j-1);
					
					for(y=1;y<nrow;y++) {
						for(x=1;x<j;x++) {
							
							if(abs(i-y)<=abs(j-x)) {
								
								if(modulation_y_man[y][x]) {
									distance=sqrt((double)((y-i)*(y-i))+(double)((x-j)*(x-j)));
									
									if(distance<mindistance) {
										otheri=y;
										otherj=x;
										mindistance=distance;
										othermod=modulation_y_man[y][x];
									}
								}
							}
						}
					}
					
					//printf("\tConnecting to [%d][%d] -> %d\n",otheri,otherj,othermod);
					
					slope=(double)(i-otheri)/(j-otherj);
					
					//printf("\tSlope: %f\n",slope);
					
					for(x=otherj;x<j;x++) {
						
						y=rint((double)otheri+slope*(double)(x-otherj));
						distance=sqrt((double)((y-i)*(y-i))+(double)((x-j)*(x-j)));
						
						modulation_y_web[y][x]=rint(((double)mod*(mindistance-distance)+(double)othermod*distance)/mindistance);
						
						//printf("\tExtrapolation for [%d][%d] -> Distance: %f, Total distance: %f, Mod: %d, Othermod: %d, Modulation: %d\n",y,x,distance,mindistance,mod,othermod,modulation_x_web[y][x]);
					}
				}
				
				//right
				if(j<ncol) {
					
					otherj=ncol;
					otheri=i;
					
					mod=modulation_y_man[i][j];
					othermod=modulation_y_man[i][j];
					
					mindistance=(double)(ncol-1);
					
					for(y=1;y<=nrow;y++) {
						for(x=j+1;x<=ncol;x++) {
							
							if(abs(i-y)<=abs(j-x)) {
								
								if(modulation_y_man[y][x]) {
									distance=sqrt((double)((y-i)*(y-i))+(double)((x-j)*(x-j)));
									
									if(distance<mindistance) {
										otheri=y;
										otherj=x;
										mindistance=distance;
										othermod=modulation_y_man[y][x];
									}
								}
							}
						}
					}
					
					//printf("\tConnecting to [%d][%d] -> %d\n",otheri,otherj,othermod);
					
					slope=(double)(otheri-i)/(otherj-j);
					
					//printf("\tSlope: %f\n",slope);
					
					for(x=j+1;x<=otherj;x++) {
						
						y=rint((double)i+slope*(double)(x-j));
						distance=sqrt((double)((y-i)*(y-i))+(double)((x-j)*(x-j)));
						
						modulation_y_web[y][x]=rint(((double)mod*(mindistance-distance)+(double)othermod*distance)/mindistance);
						
						//printf("\tExtrapolation for [%d][%d] -> Distance: %f, Total distance: %f, Mod: %d, Othermod: %d, Modulation: %d\n",y,x,distance,mindistance,mod,othermod,modulation_x_web[y][x]);
					}
				}
			}
			);
	printf("Connected fixed points\n");
}

void UpdateModulation()
{
	int x,y;
	double distance=0,distance2=0;
	int modx1=0,modx2=0,mody1=0,mody2=0;
	double ratio;
	int targetmodx,targetmody;
	
	int color1,color2;
	
	printf("Updating modulation plane\n");
	
	PLANE(
			if(modulation_x_web[i][j]) {
				modulation_x[i][j]=modulation_x_web[i][j];
			}
			
			else {
				
				//printf("Updating: %d,%d\n",i,j);
				//printf("\t:original: %d,%d\n",modulation_y[i][j],modulation_x[i][j]);
				modx1=1;
				distance=(double)(j-1);
				for(x=1;x<j;x++) {
					if(modulation_x_web[i][x]) {
						distance=(double)j-x;
						modx1=modulation_x_web[i][x];
					}
				}
				
				modx2=ncol1;
				distance2=(double)(ncol-j);
				for(x=ncol;x>j;x--) {
					if(modulation_x_web[i][x]) {
						distance2=(double)x-j;
						modx2=modulation_x_web[i][x];
					}
				}
				
				distance+=distance2;
				ratio=distance2/distance;
				targetmodx=rint((1.0-ratio)*(double)modx2+ratio*(double)modx1);
				
				modulation_x[i][j]=targetmodx;
			}
			
			if(modulation_y_web[i][j]) {
				modulation_y[i][j]=modulation_y_web[i][j];
			}
			
			else {
			
				mody1=1;
				distance=(double)i-1;				
				for(y=1;y<i;y++) {
					if(modulation_y_web[y][j]) {
						distance=(double)i-y;
						mody1=modulation_y_web[y][j];
					}
				}
				
				mody2=nrow1;
				distance2=(double)(nrow-i);
				for(y=nrow;y>i;y--) {
					if(modulation_y_web[y][j]) {
						distance2=(double)y-i;
						mody2=modulation_y_web[y][j];
					}
				}
				
				distance+=distance2;
				ratio=distance2/distance;
				targetmody=rint((1.0-ratio)*(double)mody2+ratio*(double)mody1);
				
				modulation_y[i][j]=targetmody;
			}
			
			
			
			);
	
	PLANE(
			x=modulation_x[i][j];
			y=modulation_y[i][j];
			
			color1=Code2Color(state[y][x],0);			
			color2=Code2Color(state2[i][j],0);
			
			state3[i][j]=RGB2Code(color1,color2,color1);
			);
}

void MouseClicks(int mousestroke,int mouse_i,int mouse_j)
{
	int x,y;
	x=NewIndexWrap(mouse_j,ncol);
	y=NewIndexWrap(mouse_i,nrow);
	
	if(mouse_i>nrow) {
		
		if(mousestroke==1) {
			if(mouse_j<=ncol) {
				currentx1=x;
				currenty1=y;
			}
			else {
				currentx2=x;
				currenty2=y;
				
				linkedx=modulation_x[y][x];
				linkedy=modulation_y[y][x];
			}
		}
	}
}

void KeyboardUsage(int key,int mouse_i,int mouse_j)
{
	/*
	 h                      this help information
	 q                      close graphical output (simulation continues)
	 +/=                    zoom in
	 -                      zoom out
	 f                      fullscreen mode on/off
	 arrow keys             move image
	 r                      reset display
	 */
	
	switch (key) {
			
			//general keys
			
		case 'L':
			LinkPoints();
			break;
			
		case 'U': 
			UpdateDirections();
			UpdateModulation();
			break;
			
		case 'C':
			complete=1;
			break;
			
		default:
			break;
	}
}

int main(int argc,char *argv[])
{	
	int x,y;
	int color1,color2;
	
	boundary=FIXED;
	
	// check # of arguments
	if(argc!=3){ 
		fprintf(stdout,"usage: %s image1 image2\n",argv[0]);
		exit(EXIT_FAILURE);
	}
	
	ColorFullRGB();
	
	//read size of images
	ReadSizePNG(&nrow1,&ncol1,argv[1]);
	ReadSizePNG(&nrow2,&ncol2,argv[2]);
	nrow=max(nrow1,nrow2);
	ncol=max(ncol1,ncol2);
	
	printf("nrow1: %d, ncol1: %d\n",nrow1,ncol1);
	printf("nrow2: %d, ncol2: %d\n",nrow2,ncol2);
	
	// allocate planes
	state=New();
	state2=New();
	state3=New();
	
	tempstate=New();
	
	modulation_x=New();
	modulation_y=New();
	
	modulation_x_man=New();
	modulation_y_man=New();
	
	modulation_x_west_i=New();
	modulation_x_west_j=New();
	modulation_x_east_i=New();
	modulation_x_east_j=New();
	
	modulation_y_south_i=New();
	modulation_y_south_j=New();
	modulation_y_north_i=New();
	modulation_y_north_j=New();
	
	modulation_x_web=New();
	modulation_y_web=New();
	
	//activate mouse and keyboard	
	keyboard=&KeyboardUsage;
	mouse=&MouseClicks;	
	
	// open display
	OpenDisplay("Tissue tracking",2*nrow,3*ncol);
	
	PLANE(
			state[i][j]=0;
			state2[i][j]=0;
			state3[i][j]=0;
			);
	DisplayGraphics();
	
	// read images
	ReadSizePNG(&nrow,&ncol,argv[1]);
	ReadPNG(state,1,1,argv[1]);
	
	ReadSizePNG(&nrow,&ncol,argv[2]);
	ReadPNG(state2,1,1,argv[2]);
	
	nrow=max(nrow1,nrow2);
	ncol=max(ncol1,ncol2);
	
	// set initial modulation
	mod_x=(double)(ncol1-ncol2)/(double)(ncol2-1);
	mod_y=(double)(nrow1-nrow2)/(double)(nrow2-1);
	printf("modulation_x: %f, modulation_y: %f\n",mod_x,mod_y);
	
	//set initial transformation
	PLANE(
			x=rint((double)j+(double)(j-1)*mod_x);
			if(x<1 || x>ncol1) printf("Warning -> x: %d, j:%d, mod_x: %f\n",x,j,mod_x);
			x=max(1,x);
			x=min(ncol1,x);
			
			y=rint((double)i+(double)(i-1)*mod_y);
			if(y<1 || y>nrow1) printf("Warning -> y: %d, i:%d, mod_y: %f\n",y,i,mod_y);
			y=max(1,y);
			y=min(nrow1,y);
			
			modulation_x[i][j]=x;
			modulation_y[i][j]=y;
			);
	
	PLANE(
			x=modulation_x[i][j];
			y=modulation_y[i][j];
			
			color1=Code2Color(state[y][x],0);			
			color2=Code2Color(state2[i][j],0);
			
			state3[i][j]=RGB2Code(color1,color2,color1);
			);
	
	complete=0;
	while(!complete) {
		
		DisplayGraphics();
		usleep(100);
	}
	
	return 0;
}
