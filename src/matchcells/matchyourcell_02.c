#include <excal3d2.h>

//This code takes two segmentended images, find the x-y coordinates, calculate the L numbers and finds the cell that resemble the most to a given image.
//Functions relevant from the extraction of cell outlines: DetermineTotalNoOfCells; RemoveIsolatedPixels();UpdateCells();SelectCells();SaveCellOutlines();AssignPerimeter;RunOutline2D;ReadData
//Functions relevant from EFA coefficients and L calculation:CalculateReconstruction();CalculateLcoefficients();

//from shapecomplexity_06.c
static TYPE ***original;
static TYPE ****reconstructed;
static TYPE ****xor;
static double **difference;
static double **marginaldifference;
static FLOAT ***squaredifference;

#define CELLWALL 0
#define PAVEMENTCELL 1
#define STOMATA 2
#define TOTALCELLTYPES 3

//Check noofcells: noofdifferentcells vs noofcells
static int nooftimepoints,inoofharmonicsanalyse,totalcelltypes;
static int maximumsigma=0;

typedef struct extras {
  int cellnumber;
  int timepoint;
  int oldsigma;
  int noofpoints;
  int xoffset; //offset in plane to allow reconstruction to fit in plane
  int yoffset;
  int minx;
  int maxx;
  int miny;
  int maxy;
  int width;
  int height;
  int cellarea;
  int *x;
  int *y;
  int *t1;
  int *t2;
  double *t;
  double *tdivbyT;
  double *a;
  double *b;
  double *c;
  double *d;
  double *anew;
  double *bnew;
  double *cnew;
  double *dnew;
  double *a1;// coefficients coming from L-calculation
  double *a2;
  double *b1;
  double *b2;
  double *c1;
  double *c2;
  double *d1;
  double *d2;
  double *lambda1;
  double *lambda2;
  double *newlambda1;
  double *newlambda2;
  double *arotate;
  double *brotate;
  double *crotate;
  double *drotate;
  double *L;
  double *marginaldifference;
  double angle;
  double cumulativedifference;
  double *proportion;
  double totalproportion; 
  double entropy;
  double *squaredistance;
} Extras;

#define EXTRAS ((Extras*)(reconstructedcells.extras))

static Cell originalcells,reconstructedcells;
static int totalcells=0;

//general
static int run=0,runlobe=0;

extern void (*mouse)(int,int,int);
extern void (*keyboard)(int,int,int);
extern int (*newindex)(int,int);
extern int nrow,ncol;
extern int specialcelltype;
extern int maxdistance;
extern TYPE boundaryvalue;
extern int boundary,scale,grace;
extern double nearbyint(double);

//from outline2D_02.c
typedef struct outlineextras {
  int valid;
  int startx; 
  int starty;
  int i_perimeter;
  double f_perimeter;
} Outlineextras;

#define MAXTYPES      2
#define OUTLINEEXTRAS ((Outlineextras*)(cells.extras))

static Cell cells;
static TYPE ***image;
static TYPE **state,**outline,**stateIO;
static FLOAT **f_outline;
static TYPE **xpositions=NULL,**ypositions=NULL;
static FLOAT **d_center=NULL,**d_outline=NULL;

  

//static TYPE **state_oldsigma;
//static TYPE **statet00;
//static TYPE **statet01;

static char outputdirname[STRING],outputfilename[STRING];

static int maxcells=0,ncells=0;
static int currentz;

static int biggestCellOnly;
static int excludeEdgeCells,excludeOutliersSize;
static int saveAverages,saveCellData,saveCellPositions,saveCellOutlines;

static int *neighy=NULL,*neighx=NULL;

extern int nrow,ncol,nlay,scale;
extern int specialcelltype;
static int imagewidth,imageheight;

static Png png;
static char readcells[STRING];
static char readimage[STRING];
//match your cell
double min=0; 
int location=1;

static char readcells[STRING];
//static char readcellst00[STRING];

//static char readdata[STRING];
//static char dirname[STRING];
//static int first=2000,second=2125,third=2250,fourth=2375,fifth=2500,sixth=2625,seventh=2750,eighth=2875,nineth=3000;
static TYPE **state_displaycellproperties;
static TYPE **image_displaycellproperties; 
static TYPE **state_oldsigma;
//static int imagewidth,imageheight;
//static int maximumsigma=0;

void MyInDat(char filename[],char *format,char *text,void *value)
{
  if(!InDat(filename,format,text,value)) {
    printf("cannot find \"%s\" in parameter file; exitting now!\n",text);
    exit(EXIT_FAILURE);
  }
}

void SetPars(char name[])
{
  char conversion[10];

#ifdef _SMALL
  snprintf(conversion,10,"%%f");
#else
  snprintf(conversion,10,"%%lf");
#endif

  ReadOptions(name);
  //MyInDat(name,"%d","",&);
  //MyInDat(name,conversion,"",&);
  MyInDat(name,"%d","biggestCellOnly",&biggestCellOnly); 
  MyInDat(name,"%d","excludeEdgeCells",&excludeEdgeCells); 
  MyInDat(name,"%d","excludeOutliersSize",&excludeOutliersSize); 
  MyInDat(name,"%d","saveAverages",&saveAverages);
  MyInDat(name,"%d","saveCellData",&saveCellData);
  MyInDat(name,"%d","saveCellPositions",&saveCellPositions);
  MyInDat(name,"%d","saveCellOutlines",&saveCellOutlines);
  MyInDat(name,"%d","inoofharmonicsanalyse",&inoofharmonicsanalyse);
  MyInDat(name,"%d","totalcelltypes",&totalcelltypes);
}

int DetermineTotalNoOfCells(int ac,char *av[])
{
  //this is old SetUp() function
  int i,j,k,tmpncol=0,tmpnrow=0,tmpncells=0;
  TYPE **totaldifferentcells;
  int cellnumber=0;

  //read size of image(s)
  nlay=ac-4;
  nooftimepoints=nlay;

  for(k=4;k<ac;k++) {
    ReadSizePNG(&nrow,&ncol,av[k]);
    tmpnrow=max(tmpnrow,nrow);
    tmpncol=max(tmpncol,ncol);
  }
  nrow=tmpnrow;
  ncol=tmpncol;  

  //allocate planes and colors
  image=New3D();
  PLANE(image[i][j]=NewPillar3D(););
  state=New();
  outline=New();
  xpositions=New();
  ypositions=New();
  stateIO=New();
  
  f_outline=FNew();
  d_center=FNew();
  d_outline=FNew();

  //read image(s)
  for(k=4;k<ac;k++) {
    ReadSizePNG(&nrow,&ncol,av[k]);
    ReadPNG(stateIO,1,1,av[k]);
    PLANE(image[i][j][k-3]=stateIO[i][j];);
  }
  nrow=tmpnrow;
  ncol=tmpncol;  
  printf("max nrow: %d, max ncol: %d\n",nrow,ncol);

  //determine ncells
  for(k=1;k<=nlay;k++) {
    ReadSizePNG(&nrow,&ncol,av[k+3]);
    ncells=0;
    PLANE(ncells=max(ncells,image[i][j][k]););
    tmpncells=max(tmpncells,ncells);
  }
  ncells=tmpncells;
  nrow=tmpnrow;
  ncol=tmpncol;  
  
  if(!ncells) {
    fprintf(stdout,"Warning: no cells in images error in SetUp function!\n");
    exit(EXIT_FAILURE); 
  }
  maxcells=ncells+1;
  printf("max cells in image(s): %d\n",maxcells);
  ncells=0;

  //what is highest number of cells?
  totaldifferentcells=NewPlane(nlay,maxcells-1);
  //register each cell that exists
  PLANE3D(image,
	  if(image[i][j][k])
	    totaldifferentcells[k][image[i][j][k]]=1;
	  );

  for(i=1;i<=nlay;i++)
    for(j=1;j<maxcells;j++)
      if(totaldifferentcells[i][j])
	cellnumber++;
	//printf("in frame %d there is a cell with sigma=%d\n",i,j);
  
  //allocate cells
  CNew(&cells,maxcells,MAXTYPES);
  if((cells.extras=(void *)calloc((size_t)maxcells,sizeof(Extras)))==NULL) {
    fprintf(stderr,"error in memory allocation\n");
    exit(EXIT_FAILURE);
  }
  
  InitCellPosition(&cells);
  
  //define special neighbourhood
  if((neighy=(int *)realloc(neighy,(size_t)(8*sizeof(int))))==NULL) {
    fprintf(stderr,"error in memory allocation\n");
    exit(EXIT_FAILURE);
  }
  if((neighx=(int *)realloc(neighx,(size_t)(8*sizeof(int))))==NULL) {
    fprintf(stderr,"error in memory allocation\n");
    exit(EXIT_FAILURE);
  }
  neighy[0]=0;
  neighy[1]=1;
  neighy[2]=1;
  neighy[3]=1;
  neighy[4]=0;
  neighy[5]=-1;
  neighy[6]=-1;
  neighy[7]=-1;
  
  neighx[0]=1;
  neighx[1]=1;
  neighx[2]=0;
  neighx[3]=-1;
  neighx[4]=-1;
  neighx[5]=-1;
  neighx[6]=0;
  neighx[7]=1;
  return cellnumber;
  
}

void RemoveIsolatedPixels()
{
  int removed=1,connections;
  printf("Removing isolated pixels...\n");
  while(removed) {
    removed=0;
    PLANE(
	  if(state[i][j]) {
	    connections=0;
	    NEIGHBOURS(
		       if(!(i+y==0 || j+x==0 || i+y>nrow || j+x>ncol)) {
			 if(state[i+y][j+x]==state[i][j]) connections++;
		       }
		       );
	    if(connections<3) {
	      state[i][j]=0;
	      removed++;
	    }
	  }
	  );
    printf("\t...%d isolated pixels removed...\n",removed);
  }
  printf("\t...done.\n");
}

void UpdateCells()
{
  printf("Initiating cells...\n");
  UpdateCFill(state,&cells);
  UpdateCellPosition(state,&cells);
  UpdateCellShape(&cells);
  ncells=0;
  CELLS(cells,
	if(c>specialcelltype && cells.area[c]) {
	  ncells=c;
	  OUTLINEEXTRAS[c].valid=1;
	}
	else OUTLINEEXTRAS[c].valid=0;
	);
  printf("\t...done, %d cells\n",ncells);
}

void DefineCellOutlines()
{
  int direction,next,connected,i,j,x,y;
  int maxoutline=0;
  
  printf("Calculating outline of cells\n");
  CELLS(cells, 
	printf("cell: %d, area: %d\n",c,cells.area[c]);
	if(c>specialcelltype && cells.area[c]) {
	  OUTLINEEXTRAS[c].startx=0;
	  OUTLINEEXTRAS[c].starty=0;
	}
	);
  printf("starting points reset\n");
  
  PLANE(
	if(!OUTLINEEXTRAS[state[i][j]].startx) {
	  OUTLINEEXTRAS[state[i][j]].startx=j;
	  OUTLINEEXTRAS[state[i][j]].starty=i;
	}
	);
  printf("starting points defined\n");
  
  PLANE(
	outline[i][j]=0;
	f_outline[i][j]=0.;
	);
  printf("outline reset\n");
  
  CELLS(cells, 
	if(c>specialcelltype && cells.area[c]) {
	  j=OUTLINEEXTRAS[c].startx;
	  i=OUTLINEEXTRAS[c].starty;
	  
	  OUTLINEEXTRAS[c].i_perimeter=1;
	  OUTLINEEXTRAS[c].f_perimeter=0.;

	  outline[i][j]=OUTLINEEXTRAS[c].i_perimeter;
	  f_outline[i][j]=0.;
	  
	  direction=0;
	  connected=0;

	  while(connected==0) {
	    next=0;
	    while(next==0) {
	      x=neighx[direction];
	      y=neighy[direction];
	      if(!(i+y==0 || j+x==0 || i+y>nrow || j+x>ncol) && state[i+y][j+x]==c) {
		
		next=1;
		
		i=i+y;
		j=j+x;

		if(x*y) OUTLINEEXTRAS[c].f_perimeter+=sqrt(2.);
		else OUTLINEEXTRAS[c].f_perimeter+=1.;
		
		if(!outline[i][j]) {
		  OUTLINEEXTRAS[c].i_perimeter++;
		  outline[i][j]=OUTLINEEXTRAS[c].i_perimeter;
		  f_outline[i][j]=OUTLINEEXTRAS[c].f_perimeter;
		}
		else connected=1;
		
		direction=(direction+5)%8;
	      }     
	      else direction=(direction+1)%8;
	    }
	  }
	}
	);
  printf("edge pixels defined\n");

  CELLS(cells, 
	if(c>specialcelltype && cells.area[c]) {
	  maxoutline=max(maxoutline,OUTLINEEXTRAS[c].i_perimeter);
	}
	);
  printf("oultine length defined\n");
	
  if(xpositions!=NULL) PlaneFree(xpositions);
  if(ypositions!=NULL) PlaneFree(ypositions);
  if(d_center!=NULL) FPlaneFree(d_center);
  if(d_outline!=NULL) FPlaneFree(d_outline);
  printf("memory reset\n");
  
  xpositions=NewPlane(ncells,maxoutline);
  ypositions=NewPlane(ncells,maxoutline);
  d_center=FNewPlane(ncells,maxoutline);
  d_outline=FNewPlane(ncells,maxoutline);
  printf("memory allocated, ncells: %d, maxoutline, %d\n",ncells,maxoutline);
  
  PLANE(
	//if(i==92) printf("i: %d, j: %d, outline: %d, state: %d\n",i,j,outline[i][j],state[i][j]);
	if(outline[i][j]) {
	  ypositions[state[i][j]][outline[i][j]]=i;
	  xpositions[state[i][j]][outline[i][j]]=j;
	  d_center[state[i][j]][outline[i][j]]=sqrt(pow((double)(cells.shape[state[i][j]].meany-i),2.)+pow((double)(cells.shape[state[i][j]].meanx-j),2.));
	  d_outline[state[i][j]][outline[i][j]]=f_outline[i][j];
	}
	);
  printf("outlines calculated\n");
}

void CalculateCellData()
{
  printf("CalculateCellData() not implemented yet\n");
}
    
void SelectCells()
{
  int currentcell=0;
  int currentvalue=0;
  printf("Selecting cells...\n");
  
  if(excludeEdgeCells) {
    PLANE(if(state[i][j] && (i==1 || i==nrow || j==1 || j==ncol)) OUTLINEEXTRAS[state[i][j]].valid=0;);
  }

  if(biggestCellOnly) {
    CELLS(cells,if(c>specialcelltype && OUTLINEEXTRAS[c].valid) {
	if(cells.area[c]>currentvalue) {
	  OUTLINEEXTRAS[currentcell].valid=0;
	  currentcell=c;
	  currentvalue=cells.area[c];
	}
	else OUTLINEEXTRAS[c].valid=0;
      }
      );
  }
  
  ncells=0;
  CELLS(cells,if(c>specialcelltype && OUTLINEEXTRAS[c].valid) ncells=c;);
  printf("\t...done, %d cells selected in SelectCells.\n",ncells);
    
    
}
    
void CalculateAverages()
{
   printf("CalculateAverages() not implemented yet\n");
}

void RemoveOutliers()
{
   printf("RemoveOutliers() not implemented yet\n");
}

void SaveAverages()
{
  FILE *fp;
  double average_cellsize=0.;
  
  printf("ncells: %d\n",ncells);
  CELLS(cells,if (c>specialcelltype && cells.area[c]) average_cellsize+=(double)cells.area[c];);
  average_cellsize/=(double)ncells;
  printf("average cell size: %f\n",average_cellsize);
  
  if((fp=fopen(outputfilename,"a"))==NULL) {
    fprintf(stderr,"warning: could not open a file to write average cell characterisitcs: %s\n",outputfilename);
    exit(EXIT_FAILURE);
  }
  printf("Writing overall cell characteristics...\n");
  fprintf(fp,"1. Average cell characteristics\n\n");
  fprintf(fp,"Number of cells: %d\n",ncells);
  fprintf(fp,"Average cells size: %f\n",average_cellsize);		
  fprintf(fp,"\n\n");		
  fclose(fp);
  printf("\t...done.\n");

}

void SaveCellData()
{
  FILE *fp;
  
  if((fp=fopen(outputfilename,"a"))==NULL) {
    fprintf(stderr,"warning: could not open a file to write individual cell characterisitcs: %s\n",outputfilename);
    exit(EXIT_FAILURE);
  }
  printf("Writing individuall cell characterisitcs...\n");
  fprintf(fp,"Cell data\n\n");
  CELLS(cells, 
	if(c>specialcelltype && OUTLINEEXTRAS[c].valid) {
	  fprintf(fp,"Cell: %d\n",c);
	  fprintf(fp,"size: %d\n",cells.area[c]);
	  fprintf(fp,"meanx: %f\n",cells.shape[c].meanx);
	  fprintf(fp,"meany: %f\n",cells.shape[c].meany);
	  fprintf(fp,"\n");
	}
	);
  fprintf(fp,"\n");		
  fclose(fp);
  printf("\t...done.\n");
}

void SaveCellPositions()
{
  FILE *fp;
    
  if((fp=fopen(outputfilename,"a"))==NULL) {
    fprintf(stderr,"warning: could not open a file to write individual cell position: %s\n",outputfilename);
    exit(EXIT_FAILURE);
  }
  printf("Writing individuall cell positions...\n");
  fprintf(fp,"Indivdual cell positions\n\n");
  CELLS(cells, 
	if(c>specialcelltype && OUTLINEEXTRAS[c].valid) {
	  fprintf(fp,"Surface cell %d\n",c);
	  PLANE(if(state[i][j]==c) fprintf(fp,"%d\t%d\n",j,i););
	  fprintf(fp,"\n");
	}
	);
  fprintf(fp,"\n");		
  fclose(fp);
  printf("\t...done.\n");
}

void SaveCellOutlines()
{
  FILE *fp;
  int i;
    
  if((fp=fopen(outputfilename,"a"))==NULL) {
    fprintf(stderr,"warning: could not open data-file: %s\n",outputfilename);
    exit(EXIT_FAILURE);
  }
  printf("Writing individuall cell outlines...\n");
  //fprintf(fp,"Cell outlines\n\n");
  CELLS(cells, 
	if(c>specialcelltype && OUTLINEEXTRAS[c].valid) {
	  fprintf(fp,"Outline cell %d\n",c);
	  fprintf(fp,"Index\tX-position\tY-position\tLength\tRel.Length\tDistance.Center\tArea\n");
	  for(i=1;i<=OUTLINEEXTRAS[c].i_perimeter;i++) {
	    fprintf(fp,"%d\t%d\t%d\t%f\t%f\t%f\t%d\n",i,xpositions[c][i],ypositions[c][i],d_outline[c][i],d_outline[c][i]/OUTLINEEXTRAS[c].f_perimeter,d_center[c][i],cells.area[c]);
	  }
	  fprintf(fp,"%d\t%d\t%d\t%f\t%f\t%f\t%d\n",OUTLINEEXTRAS[c].i_perimeter+1,xpositions[c][1],ypositions[c][1],OUTLINEEXTRAS[c].f_perimeter,1.,d_center[c][1],cells.area[c]);
	  fprintf(fp,"\n");
	  //printf(" c and x: %d\t%d\n",c,xpositions[c][i]);
	}
	);
  fprintf(fp,"\n");		
  fclose(fp);
  printf("\t...done.\n");
}

void AssignPerimeter(int cellnumber,int timepoint,int oldsigma,int noofpoints,int *y,int *x, int cellarea)
{
  int i;

  totalcells++;
  //printf("%d/n",totalcells);
  EXTRAS[totalcells].cellnumber=cellnumber;
  //to make timepoint 0 equal to frame 00000.png
  EXTRAS[totalcells].timepoint=timepoint-1;
  EXTRAS[totalcells].oldsigma=oldsigma;
  EXTRAS[totalcells].noofpoints=noofpoints;
  EXTRAS[totalcells].noofpoints+=1; //becuase we want startingpoint to be end-point as well
  EXTRAS[totalcells].cellarea=cellarea;
   if(EXTRAS[totalcells].cellnumber<totalcelltypes)
    originalcells.celltype[totalcells]=EXTRAS[totalcells].cellnumber;
  else {
    fprintf(stderr,"cellnumber larger or equal than totalcelltypes (%d>=%d)! Exitting now!\n",EXTRAS[totalcells].cellnumber,totalcelltypes);
    exit(EXIT_FAILURE);
  }   

  if(
     ((difference[totalcells]=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((marginaldifference[totalcells]=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((reconstructed[totalcells]=(TYPE***)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(TYPE***)))==NULL) ||
     ((xor[totalcells]=(TYPE***)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(TYPE***)))==NULL) ||
     //((squaredifference[totalcells]=(double***)calloc((size_t)(inoofharmonicsanalyse),sizeof(double**)))==NULL) || 
     ((EXTRAS[totalcells].L=(double*)calloc((size_t)(inoofharmonicsanalyse+3),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].marginaldifference=(double*)calloc((size_t)(inoofharmonicsanalyse+3),sizeof(double)))==NULL) || 
     ((EXTRAS[totalcells].squaredistance=(double*)calloc((size_t)(totalcells),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].proportion=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].arotate=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].brotate=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].crotate=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].drotate=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].lambda1 =(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].lambda2=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].newlambda1=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].newlambda2=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].anew=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].bnew=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].cnew=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].dnew=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].a1=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].a2=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].b1=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].b2=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].c1=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].c2=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].d1=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].d2=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].a=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].b=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].c=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].d=(double*)calloc((size_t)(inoofharmonicsanalyse+2),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].t1=(int*)calloc((size_t)(EXTRAS[totalcells].noofpoints),sizeof(int)))==NULL) ||
     ((EXTRAS[totalcells].t2=(int*)calloc((size_t)(EXTRAS[totalcells].noofpoints),sizeof(int)))==NULL) ||
     ((EXTRAS[totalcells].t=(double*)calloc((size_t)(EXTRAS[totalcells].noofpoints),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].tdivbyT=(double*)calloc((size_t)(EXTRAS[totalcells].noofpoints),sizeof(double)))==NULL) ||
     ((EXTRAS[totalcells].x=(int*)calloc((size_t)(EXTRAS[totalcells].noofpoints),sizeof(int)))==NULL) ||
     ((EXTRAS[totalcells].y=(int*)calloc((size_t)(EXTRAS[totalcells].noofpoints),sizeof(int)))==NULL)) {
    fprintf(stderr,"ReadData: error in memory allocation\n");
    exit(EXIT_FAILURE);
  }

  for(i=0;i<EXTRAS[totalcells].noofpoints;i++) { //note that one more datapoint has to be assigned, as last point is first point
    if(i<EXTRAS[totalcells].noofpoints-1) {
      EXTRAS[totalcells].x[i]=x[i];
      EXTRAS[totalcells].y[i]=y[i];
      //printf("%d %d %d %d\n",totalcells,i,EXTRAS[totalcells].x[i],EXTRAS[totalcells].y[i]);
    }
    else {
      //last is equal to first
      EXTRAS[totalcells].x[EXTRAS[totalcells].noofpoints-1]=x[0];
      EXTRAS[totalcells].y[EXTRAS[totalcells].noofpoints-1]=y[0];
      //printf("%d %d %d %d\n",totalcells,i,EXTRAS[totalcells].x[EXTRAS[totalcells].noofpoints-1],EXTRAS[totalcells].y[EXTRAS[totalcells].noofpoints-1]);
    }

    if(i==0) {//first datapoint
      EXTRAS[totalcells].minx=EXTRAS[totalcells].x[i];
      EXTRAS[totalcells].maxx=EXTRAS[totalcells].x[i];
      EXTRAS[totalcells].miny=EXTRAS[totalcells].y[i];
      EXTRAS[totalcells].maxy=EXTRAS[totalcells].y[i];
      EXTRAS[totalcells].t1[i]=0;//starting point 
      EXTRAS[totalcells].t2[i]=0;
    }
    else {
      EXTRAS[totalcells].minx=min(EXTRAS[totalcells].minx,EXTRAS[totalcells].x[i]);
      EXTRAS[totalcells].maxx=max(EXTRAS[totalcells].maxx,EXTRAS[totalcells].x[i]);
      EXTRAS[totalcells].miny=min(EXTRAS[totalcells].miny,EXTRAS[totalcells].y[i]);
      EXTRAS[totalcells].maxy=max(EXTRAS[totalcells].maxy,EXTRAS[totalcells].y[i]);
      if(abs(EXTRAS[totalcells].x[i]-EXTRAS[totalcells].x[i-1])+abs(EXTRAS[totalcells].y[i]-EXTRAS[totalcells].y[i-1])==2) {//add to t2, but not t1
	EXTRAS[totalcells].t1[i]=EXTRAS[totalcells].t1[i-1];
	EXTRAS[totalcells].t2[i]=EXTRAS[totalcells].t2[i-1]+1;
      }
      else {//add to t1, but not t2
	EXTRAS[totalcells].t1[i]=EXTRAS[totalcells].t1[i-1]+1;
	EXTRAS[totalcells].t2[i]=EXTRAS[totalcells].t2[i-1];
      }
    }
  }

  //if(c==1) 
  //printf(" for c=1, noofpoints is %d ,the maxx is %d and the maxy is %d\n", EXTRAS[totalcells].noofpoints,EXTRAS[totalcells].maxx,EXTRAS[totalcells].maxy);
  //calculate t along cell boundary 
  for(i=0;i<EXTRAS[totalcells].noofpoints;i++) {
    EXTRAS[totalcells].t[i]=EXTRAS[totalcells].t1[i]+EXTRAS[totalcells].t2[i]*M_SQRT2;
    EXTRAS[totalcells].tdivbyT[i]=EXTRAS[totalcells].t[i]/(EXTRAS[totalcells].t1[EXTRAS[totalcells].noofpoints-1]+EXTRAS[totalcells].t2[EXTRAS[totalcells].noofpoints-1]*M_SQRT2);
    //if(c==1)
    //printf(" for c=1 index %d, and x=%d, t is %lf, t1 is %d, t2 is %d\n",i,EXTRAS[totalcells].x[i],EXTRAS[totalcells].t[i],EXTRAS[totalcells].t1[i],EXTRAS[totalcells].t2[i]);
  }
  
  //if(c==1) 
  //{
  //printf(" for c=1, noofpoints is %d ,the maxx is %d and the maxy is %d, the minx is %d and miny is %d\n", EXTRAS[c].noofpoints,EXTRAS[c].maxx,EXTRAS[c].maxy,EXTRAS[c].minx,EXTRAS[c].miny);
  //}
  EXTRAS[totalcells].width=EXTRAS[totalcells].maxx-EXTRAS[totalcells].minx+1;
  EXTRAS[totalcells].height=EXTRAS[totalcells].maxy-EXTRAS[totalcells].miny+1;
}

void RunOutline2D(int ac,char *av[]) //which contains AssignPerimeter
{
  for (currentz=1;currentz<=nlay;currentz++) {
    ReadSizePNG(&nrow,&ncol,av[currentz+3]);
    PLANE(
	  state[i][j]=0;
	  outline[i][j]=0;
	  f_outline[i][j]=0.;
	  );
    PLANE(state[i][j]=image[i][j][currentz];);
    
    RemoveIsolatedPixels(); 
    UpdateCells();
    DefineCellOutlines();
    CalculateCellData();
    SelectCells();
    if(ncells>1) CalculateAverages();
    if(ncells>1) RemoveOutliers();

    CELLS(cells, 
	  if(c>specialcelltype && OUTLINEEXTRAS[c].valid) {
	    AssignPerimeter(1 /*cellnumber, currently just always 1*/,currentz /*timepoint*/,c /*sigma*/,OUTLINEEXTRAS[c].i_perimeter /*number of points*/,&ypositions[c][1],&xpositions[c][1],cells.area[c]);
	  }
	  );
    
    /*
    if((fp=fopen(outputfilename,"a"))==NULL) {
      fprintf(stderr,"warning: could not open data-file: %s\n",outputfilename);
      exit(EXIT_FAILURE);
    }
    if(ncells) {
      fprintf(fp,"Data for cells in: %s\n\n",argv[currentz+2]);
      fclose(fp);
      if(saveAverages) SaveAverages();
      if(saveCellData) SaveCellData();
      if(saveCellPositions) SaveCellPositions();
      if(saveCellOutlines) SaveCellOutlines();
    }
    else {
      fprintf(fp,"No cells selected in: %s\n\n",argv[currentz+2]);
      fclose(fp);
    }
    */
  }   
}

void ReadData(int ac,char *av[])
{
  FILE *fp;
  int i;
  int maxwidth=0,maxheight=0;
  char a_string[STRING];

  //check # of arguments
  if(ac<6){
    fprintf(stdout,"usage: %s parfile output_dirname [orginal_tissueImage] [segmented image at t=0] [segmented image at t=1]\n",av[0]);
    exit(EXIT_FAILURE);
  }

  //create outputdir
  if(snprintf(outputdirname,STRING,"%s",av[2])>=STRING) {
    outputdirname[0]=toupper(outputdirname[0]);
    fprintf(stderr,"warning: outputdirname too long: %s\n",outputdirname);
  }
  outputdirname[0]=toupper(outputdirname[0]);
  snprintf(a_string,STRING,"mkdir -p %s",outputdirname);
  system(a_string);

  //create outputfilename
  if(snprintf(outputfilename,STRING,"%s/%s.dat",outputdirname,av[2])>=STRING){
    fprintf(stderr,"warning: filename for log too long: %s\n",outputfilename);
  }

  //writing outputfilename header
  if((fp=fopen(outputfilename,"w"))==NULL) {
    fprintf(stderr,"warning: could not open a file to write header: %s\n",outputfilename);
    exit(EXIT_FAILURE);
  }
  fprintf(fp,"data analyzed with %s\n",av[0]);
  fclose(fp);
  
  //read parameters
  fprintf(stdout,"reading parameters from %s\n",av[1]);
  SetPars(av[1]); 
  
  if(snprintf(a_string,STRING,"%s/%s.par",outputdirname,av[2])>=STRING)
    fprintf(stderr,"warning: parfile name too long: %s\n",a_string);
  else
    SaveOptions(av[1],a_string);
  
  //now we need to know how many cells we will have, as well as setting of nooftimepoints
  //this will be overestimation of totalcells, since each picture will contain cells that are not valid
  //we therefore keep the more serious allocation to later on, limited to cells we are really interested in

  //so first time (after DetermineTotalNoOfCells) totalcells will be bigger than second time (after RunOutline2D)
  totalcells=DetermineTotalNoOfCells(ac,av);
  

  CNew(&originalcells,totalcells+1,totalcelltypes); //maxsigma+1 because we have to count 0 as well
  CNew(&reconstructedcells,totalcells+1,totalcelltypes); //maxsigma+1 because we have to count 0 as well
  if((reconstructedcells.extras=(void *)calloc((size_t)reconstructedcells.maxcells,sizeof(Extras)))==NULL) {
    fprintf(stderr,"ReadData: error in memory allocation\n");
    exit(EXIT_FAILURE);
  }
  
  //two reasons why each cell in different plane:
  //1) much more easy to determine inside/outside of cell
  //2) reconstruction of different cells could overlap
  if(((original=(TYPE***)calloc((size_t)reconstructedcells.maxcells,sizeof(TYPE**)))==NULL) ||
     ((difference=(double**)calloc((size_t)reconstructedcells.maxcells,sizeof(double*)))==NULL) ||
     ((marginaldifference=(double**)calloc((size_t)reconstructedcells.maxcells,sizeof(double*)))==NULL) ||
     ((reconstructed=(TYPE****)calloc((size_t)reconstructedcells.maxcells,sizeof(TYPE***)))==NULL) ||
     ((squaredifference=(double***)calloc((size_t)reconstructedcells.maxcells,sizeof(double***)))==NULL) ||
     ((xor=(TYPE****)calloc((size_t)reconstructedcells.maxcells,sizeof(TYPE***)))==NULL)) {
    fprintf(stderr,"ReadData: error in memory allocation\n");
    exit(EXIT_FAILURE);
  }
  
  //let's make sure that missing cells have no timepoints
  //because some cells will not be valid
  CELLS(originalcells,
	EXTRAS[c].noofpoints=0;
	);
  
  totalcells=0;
  //now really read in
  RunOutline2D(ac,av); //which contains AssignPerimeter
  
  //how big do we need it?
  CELLS(originalcells,
	if(EXTRAS[c].noofpoints) {
	  if(EXTRAS[c].width>maxwidth)
	    maxwidth=EXTRAS[c].width;
	  if(EXTRAS[c].height>maxheight)
	    maxheight=EXTRAS[c].height;
	}
	);
 
  printf("maxwidth %d maxheight %d\n",maxwidth,maxheight);
  //let's make the planes twice as large as the longest axis. There was a problem with memory allocation for big images...check
  nrow=max(maxwidth,maxheight)+50;
  ncol=nrow;
  printf("ncol %d and nrow %d\n", ncol, nrow);
  //how much sticks out on each side?
  CELLS(originalcells,
	if(EXTRAS[c].noofpoints) {
	  EXTRAS[c].xoffset=(ncol-EXTRAS[c].width)/2-EXTRAS[c].minx+1;
	  EXTRAS[c].yoffset=(nrow-EXTRAS[c].height)/2-EXTRAS[c].miny+1;
	  original[c]=New();
	  for(i=0;i<inoofharmonicsanalyse+2;i++) {
	    reconstructed[c][i]=New();
	    xor[c][i]=New();
	  }
	}
	//if(c==1) 
	);
  CELLS(reconstructedcells,
	if(EXTRAS[c].noofpoints) {
	  //printf("cell %d\txoffset= %d\tyoffset =%d\twidth=%d\t height=%d\tmaxx=%d maxy=%d\tminx=%d miny=%d\t time=%f\t noofpoints=%d\n",c, EXTRAS[c].xoffset,EXTRAS[c].yoffset, EXTRAS[c].width,EXTRAS[c].height,EXTRAS[c].maxx,EXTRAS[c].maxy,EXTRAS[c].minx,EXTRAS[c].miny,EXTRAS[c].t[EXTRAS[c].noofpoints-1],EXTRAS[c].noofpoints);
	  //printf("cell %d\t time=%f\t noofpoints=%d\n",c,EXTRAS[c].t[EXTRAS[c].noofpoints-1],EXTRAS[c].noofpoints);
	  //printf(" for c=16,the maxx is %d and the maxy is %d and the minx is %d and the miny is %d\n",EXTRAS[16].maxx,EXTRAS[16].maxy,EXTRAS[16].minx,EXTRAS[16].miny);
	}
	);
  //printf("EXTRAS[1].xoffset is %d and yoffset is %d the width is %d and the height is %d\n", EXTRAS[1].xoffset,EXTRAS[1].yoffset,EXTRAS[1].width,EXTRAS[1].height);
  //printf(" for c=1,the maxx is %d and the maxy is %d and the minx is %d and the miny is %d\n",EXTRAS[1].maxx,EXTRAS[1].maxy,EXTRAS[1].minx,EXTRAS[1].miny );
  ColorTable(0,0,WHITE);
  ColorRandom(1,totalcelltypes-1);
  ColorGrad(ColorName(10000,10000,"green"),ColorName(10000+nooftimepoints,10000+nooftimepoints,"red"));
  
  /*
    for(c=1;c<=totalcells;c++) {
    printf("%d\t%d\t%d\t%d\n",EXTRAS[c].cellnumber,EXTRAS[c].timepoint,EXTRAS[c].oldsigma,EXTRAS[c].noofpoints);
    for(i=0;i<EXTRAS[c].noofpoints;i++)
    printf("%d\t%d\t%d\n",i,EXTRAS[c].x[i],EXTRAS[c].y[i]);
    }
  */
} 

void FillOriginalDataPlanes()
{
  int i;

  CELLS(originalcells,
	for(i=0;i<EXTRAS[c].noofpoints;i++)
	  original[c][(EXTRAS[c].yoffset+EXTRAS[c].y[i])][(EXTRAS[c].xoffset+EXTRAS[c].x[i])]=c;
	);
}

void CheckPosition(TYPE **a,int i,int j)
{
  //we found a pixel outside of cell
  a[i][j]=-1;
  if(!a[i-1][j])
    CheckPosition(a,i-1,j);
  if(!a[i+1][j])
    CheckPosition(a,i+1,j);
  if(!a[i][j-1])
    CheckPosition(a,i,j-1);
  if(!a[i][j+1])
    CheckPosition(a,i,j+1);
}

void FillShape(TYPE **a,int c)
{
	
  boundary=FIXED;
  boundaryvalue=-1;
  Boundaries(a);
  PLANE(
  if(!a[i][j] && (a[i-1][j]==-1 || a[i+1][j]==-1 || a[i][j-1]==-1 || a[i][j+1]==-1))
	  CheckPosition(a,i,j);
	);
  PLANE(
	if(!a[i][j])//pixel has not been changed into -1, so this is inside cell
	  a[i][j]=c;
	else if(a[i][j]==-1)//pixel has been changed into 0, so this is outside cell
	  a[i][j]=0;
	);
  boundaryvalue=0;
  Boundaries(a);

}

void FillOriginalShape()
{
  CELLS(originalcells,
	if(EXTRAS[c].noofpoints)
	  FillShape(original[c],c);
	);
	printf("OK FillOriginalShape\n"); 
}

void FillReconstructedShape()
{
  int lobes;

  CELLS(originalcells,
	if(EXTRAS[c].noofpoints) {
	  printf("filling in cell #%d of %d\n",c,totalcells);
	  for(lobes=1;lobes<inoofharmonicsanalyse+2;lobes++)
	    FillShape(reconstructed[c][lobes],c);
	}
	);
	printf("OK FillReconstructedShape\n"); 
}

int ReconstructedXValue(int c,int lobe,double t)
{
  //we made every new1 to go counterclockwise
  //we made every new2 to go clockwise
  //so new1 gives i-1 lobes; new2 i+1;
  //so lobe p comes from new1[p+1] and new2[p-1]
  
  double xvalue=0.;
  int p;

  // contribution from coefficients 1 (after L calculation in this code)
  //  make sure that we do not read in harmonic data that does not exist. Highest valid harmonic is inoofharmonicsanalyse
  for(p=0;p<min(lobe+2,inoofharmonicsanalyse);p++) //the last contribution to lobe comes from new1[lobe+1]
    xvalue+=EXTRAS[c].a1[p]*cos(2.*M_PI*(double)p*t)+EXTRAS[c].b1[p]*sin(2.*M_PI*(double)p*t);
  //contribution from coefficients 2 (after L calculation in this code)
  for(p=0;p<min(lobe,inoofharmonicsanalyse);p++) //the last contribution to lobe comes from new2[lobe-1]
    xvalue+=EXTRAS[c].a2[p]*cos(2.*M_PI*(double)p*t)+EXTRAS[c].b2[p]*sin(2.*M_PI*(double)p*t);
  
  return (int)nearbyint(xvalue);
}

int ReconstructedYValue(int c,int lobe,double t)
{
  //we made every new1 to go counterclockwise
  //we made every new2 to go clockwise
  //so new1 gives i-1 lobes; new2 i+1;
  //so lobe p comes from new1[p+1] and new2[p-1]
  
  double yvalue=0.;
  int p;
  
  //  contribution from coefficients 1 (after L calculation in this code) */
  for(p=0;p<min(lobe+2,inoofharmonicsanalyse);p++) //the last contribution to lobe comes from new1[lobe+1]
    yvalue+=EXTRAS[c].c1[p]*cos(2.*M_PI*(double)p*t)+EXTRAS[c].d1[p]*sin(2.*M_PI*(double)p*t);
  // contribution from coefficients 2 (after L calculation in this code)
  for(p=0;p<min(lobe,inoofharmonicsanalyse);p++) //the last contribution to lobe comes from new2[lobe-1]
    yvalue+=EXTRAS[c].c2[p]*cos(2.*M_PI*(double)p*t)+EXTRAS[c].d2[p]*sin(2.*M_PI*(double)p*t);

  return (int)nearbyint(yvalue);
}

void MindTheGap(int c,int lobes,int oldx,int x,int oldy,int y,double oldt,double t,int level)
{
  int newx,newy;
  
  newx=ReconstructedXValue(c,lobes,(oldt+t)/2.);
  newy=ReconstructedYValue(c,lobes,(oldt+t)/2.);
  reconstructed[c][lobes][newindex(newy+EXTRAS[c].yoffset,nrow)][newindex(newx+EXTRAS[c].xoffset,ncol)]=c;
  if(level>1)
    printf("mind the gap: %d %d %d (%d,%d) (%d,%d) (%d,%d) %lf %lf\n",level,c,lobes,oldx,oldy,newx,newy,x,y,oldt,t);

  if((newx-oldx)*(newx-oldx)+(newy-oldy)*(newy-oldy)>2)
    MindTheGap(c,lobes,oldx,newx,oldy,newy,oldt,(oldt+t)/2.,level+1);
  if((x-newx)*(x-newx)+(y-newy)*(y-newy)>2)
    MindTheGap(c,lobes,newx,x,newy,y,(oldt+t)/2.,t,level+1);
}

void DetermineReconstructedShape()
{
  int i;
  int lobes;
  int x,y;
  int oldx=0,oldy=0;
  
  CELLS(originalcells,
	if(EXTRAS[c].noofpoints) {
	  printf("reconstructing cell #%d of %d\n",c,totalcells);
	  for(lobes=1;lobes<inoofharmonicsanalyse+2;lobes++) {
	    for(i=0;i<EXTRAS[c].noofpoints;i++) {
	      //printf("%d\t%d\t%d\t%d\t%d\t%d\n",c,i,EXTRAS[c].x[i],ReconstructedXValue(c,i,101),EXTRAS[c].y[i],ReconstructedYValue(c,i,101));
	      x=ReconstructedXValue(c,lobes,EXTRAS[c].tdivbyT[i]);
	      y=ReconstructedYValue(c,lobes,EXTRAS[c].tdivbyT[i]);
	      reconstructed[c][lobes][newindex(y+EXTRAS[c].yoffset,nrow)][newindex(x+EXTRAS[c].xoffset,ncol)]=c;
	      if(i && ((x-oldx)*(x-oldx)+(y-oldy)*(y-oldy)>2)) //dist squared more than one pixel
		MindTheGap(c,lobes,oldx,x,oldy,y,EXTRAS[c].tdivbyT[i-1],EXTRAS[c].tdivbyT[i],1);
	      oldx=x;
	      oldy=y;
	    }
	  }
	}
	);
}

void Mouse(int mousestroke,int mouse_i,int mouse_j)
{
  int k;
  //int c=0;
  while(mouse_j>imagewidth)
    mouse_j-=imagewidth;
  while(mouse_i>imageheight)
    mouse_i-=imageheight;
  switch(mousestroke) {
  case 2:
    
    k=state[mouse_i][mouse_j];
    
    CELLS(originalcells,
	if(EXTRAS[c].noofpoints) {
    //for (i=1;i<=totalcells;i++){		 
    if (state[mouse_i][mouse_j]==EXTRAS[c].oldsigma){
		k=c;
        //printf("c=%d,k=%d\n",c,k);
    }
    }
    );
    //fprintf(stdout,"cell %d has an area of %d and L4 of %lf, and formfactor of %lf and aspectratio of %lf a PC1 of %lf, PC2 of %lf\n",k,cells.area[k],EXTRAS[k].L[4],properties[FORMFACTOR][mouse_i][mouse_j],properties[ASPECTRATIO][mouse_i][mouse_j],properties[FIRSTPC][mouse_i][mouse_j],EXTRAS[k].scores[2]);
    //fprintf(stdout,"cell %d has:oldsigma=%d\tarea=%d\tCD=%f\tentropy=%f\tformfactor=%f\tangle=%f\tL1=%f\tL2=%f\tL4=%f\tL5=%f\tL6=%f\tL7=%f\tL8=%f\tMD1=%f\tMD2=%f\tMD3=%f\tMD4=%f\tMD5=%f\tMD6=%f\tMD7=%f\tMD8=%f\n",k,EXTRAS[k].oldsigma,EXTRAS[k].cellarea,EXTRAS[k].cumulativedifference,EXTRAS[k].entropy,properties[FORMFACTOR][mouse_i][mouse_j],EXTRAS[k].angle,EXTRAS[k].Lobe1,EXTRAS[k].L[2],EXTRAS[k].L[4],EXTRAS[k].L[5],EXTRAS[k].L[6],EXTRAS[k].L[7],EXTRAS[k].L[8],EXTRAS[k].marginaldifference1,EXTRAS[k].marginaldifference2,EXTRAS[k].marginaldifference3,EXTRAS[k].marginaldifference4,EXTRAS[k].marginaldifference5,EXTRAS[k].marginaldifference6,EXTRAS[k].marginaldifference7,EXTRAS[k].marginaldifference8);
   fprintf(stdout,"cell %d oldsigma%d\n", k,EXTRAS[k].oldsigma);
    break;
  default:
    break;
  }
}

void Key(int key,int mouse_i,int mouse_j)
{
  switch(key) {
  case 'h':
    printf("\ts\tstart/stop running through timepoints\n"
	   "\tS\tstep through timepoints\n"
	   "\tA\tstep backwards through timepoints\n"
	   "\tl\tstart/stop running through lobenumber\n"
	   "\tL\tstep through lobenumber\n"
	   "\tK\tstep backwards through lobenumber\n"
	   "\n"
	   "Mouse:\n"
	   );
    break;
  case 's':
    run=!run;
    printf("%srunning\n",(run?"":"not "));
    break;
  case 'S':
    run=2;
    break;
  case 'l':
    runlobe=!runlobe;
    printf("%srunning through lobes\n",(runlobe?"":"not "));
    break;
  case 'L':
    runlobe=2;
    break;
  case 'A':
    run=3;
    break;
  case 'K':
    runlobe=3;
    break;
  default:
    break;
  }
}

void CalculateReconstruction()
{
  int k,p;
  double deltaxj,deltayj,deltatj; //as used in Kuhl & Giardina, p.240, Comp Graph & Imag Proc 18, 236--258 (1982)
  double deltaxp,deltayp,deltatp;
  double intermediate,intermediatep,intermediatepmin1;

  //InitCellPosition(&reconstructedcells);

  CELLS(reconstructedcells,
	//UpdateCFill(original[c],&reconstructedcells);
	//OneCellPosition(original[c],&reconstructedcells,c);
	
	if(EXTRAS[c].noofpoints) {
	  for(k=0;k<=inoofharmonicsanalyse;k++) {
	    EXTRAS[c].a[k]=0.;	
	    EXTRAS[c].b[k]=0.;
	    EXTRAS[c].c[k]=0.;	
	    EXTRAS[c].d[k]=0.;
	  }
	    
	  deltaxj=0.;deltayj=0.;deltatj=0.;
	  for(p=1;p<EXTRAS[c].noofpoints;p++) {
	    deltaxp=EXTRAS[c].x[p]-EXTRAS[c].x[p-1];
	    deltayp=EXTRAS[c].y[p]-EXTRAS[c].y[p-1];
	    deltatp=EXTRAS[c].t[p]-EXTRAS[c].t[p-1];
	   
	    intermediate=1./(2.*deltatp)*(EXTRAS[c].t[p]*EXTRAS[c].t[p]-EXTRAS[c].t[p-1]*EXTRAS[c].t[p-1]);
	    EXTRAS[c].a[0]+=deltaxp*intermediate+(deltaxj-deltaxp/deltatp*deltatj)*(EXTRAS[c].t[p]-EXTRAS[c].t[p-1]);	
	    EXTRAS[c].c[0]+=deltayp*intermediate+(deltayj-deltayp/deltatp*deltatj)*(EXTRAS[c].t[p]-EXTRAS[c].t[p-1]);
	    for(k=1;k<=inoofharmonicsanalyse;k++) {
	      intermediatep=2.*M_PI*(double)k*EXTRAS[c].tdivbyT[p];
	      intermediatepmin1=2.*M_PI*(double)k*EXTRAS[c].tdivbyT[p-1];

	      EXTRAS[c].a[k]+=deltaxp/deltatp*(cos(intermediatep)-cos(intermediatepmin1));	
	      EXTRAS[c].b[k]+=deltaxp/deltatp*(sin(intermediatep)-sin(intermediatepmin1));	
	      EXTRAS[c].c[k]+=deltayp/deltatp*(cos(intermediatep)-cos(intermediatepmin1));	
	      EXTRAS[c].d[k]+=deltayp/deltatp*(sin(intermediatep)-sin(intermediatepmin1));	
	      //if(c==1)
	      //printf("%d\t%d\t%lf\t%lf\t%lf\t%lf\n",c,k,EXTRAS[c].a[k],EXTRAS[c].b[k],EXTRAS[c].c[k],EXTRAS[c].d[k]); 
	      //printf("%d\t%d\t%d\t%d\t%lf\t%lf\n",EXTRAS[c].noofpoints,k,EXTRAS[c].x[k],EXTRAS[c].y[k],EXTRAS[c].t[k],EXTRAS[c].tdivbyT[p]);
	    }
	    //at the end, increase deltaxj etc, because they should always go up to p-1 instead of p
	    deltaxj+=deltaxp;
	    deltayj+=deltayp;
	    deltatj+=deltatp;
	  }
	  //if(c==16) 
	  // printf("%lf\t%lf\t%lf\t%lf\n",EXTRAS[c].a[0],EXTRAS[c].b[0],EXTRAS[c].c[0],EXTRAS[c].d[0]);
	  
	  EXTRAS[c].a[0]/=EXTRAS[c].t[EXTRAS[c].noofpoints-1];
	  EXTRAS[c].c[0]/=EXTRAS[c].t[EXTRAS[c].noofpoints-1];
	  //note, DC component is calculated relative to starting point, so we also need:
	  EXTRAS[c].a[0]+=EXTRAS[c].x[0];
	  EXTRAS[c].c[0]+=EXTRAS[c].y[0];

	  for(k=1;k<=inoofharmonicsanalyse;k++) {
	    EXTRAS[c].a[k]*=EXTRAS[c].t[EXTRAS[c].noofpoints-1]/(2.*(double)(k*k)*M_PI*M_PI);
	    EXTRAS[c].b[k]*=EXTRAS[c].t[EXTRAS[c].noofpoints-1]/(2.*(double)(k*k)*M_PI*M_PI);
	    EXTRAS[c].c[k]*=EXTRAS[c].t[EXTRAS[c].noofpoints-1]/(2.*(double)(k*k)*M_PI*M_PI);
	    EXTRAS[c].d[k]*=EXTRAS[c].t[EXTRAS[c].noofpoints-1]/(2.*(double)(k*k)*M_PI*M_PI);
	  }
	   //if(c==1) {
	  ////printf("In CalculateReconstruction\n");
	 //// printf("%lf\t%lf\t%lf\t%lf\n",EXTRAS[c].a[0],EXTRAS[c].b[0],EXTRAS[c].c[0],EXTRAS[c].d[0]);
	   //for(k=0;k<=inoofharmonicsanalyse;k++) 
	   //printf("%d\t%d\t%lf\t%lf\t%lf\t%lf\n",c,k,EXTRAS[c].a[k],EXTRAS[c].b[k],EXTRAS[c].c[k],EXTRAS[c].d[k]);
	   //}     
	  //printf("%lf %lf %lf %lf %lf %lf\n",EXTRAS[c].a[0],EXTRAS[c].a[0]+EXTRAS[c].x[0],EXTRAS[c].anew1[0],EXTRAS[c].c[0],EXTRAS[c].c[0]+EXTRAS[c].y[0],EXTRAS[c].cnew1[0]);
	  //printf("%lf %lf %lf %lf\n",reconstructedcells.shape[c].meanx-EXTRAS[c].xoffset,reconstructedcells.shape[c].meany-EXTRAS[c].yoffset,EXTRAS[c].a[0]+reconstructedcells.shape[c].meanx-EXTRAS[c].xoffset,EXTRAS[c].c[0]+reconstructedcells.shape[c].meany-EXTRAS[c].yoffset);
	}
	);
}

//From efa14.c code
void CalculateLcoefficients()
{
  int k;
  double tau,starttau1,starttau2,starttau;
  double tmplambda;
  starttau1=0;
  starttau2=0;
  CELLS(reconstructedcells,
	if(EXTRAS[c].noofpoints) {
	  // angle of first semimajor axis. tau is TEMPORAL angle after starting point to pass first semimajor axis (not always first, actually) 
	  k=1;
	  tau=atan2(2.*(EXTRAS[c].a[k]*EXTRAS[c].b[k]+EXTRAS[c].c[k]*EXTRAS[c].d[k]),EXTRAS[c].a[k]*EXTRAS[c].a[k]+EXTRAS[c].c[k]*EXTRAS[c].c[k]-EXTRAS[c].b[k]*EXTRAS[c].b[k]-EXTRAS[c].d[k]*EXTRAS[c].d[k])/2.; 
	  /*  if(c==1) */
	  /*   fprintf(stdout,"tau: %lf\n", tau); */
	  //rotating ellipse tau brings semim axis to starting point  
	  //Kuhl, cgip82 
	  for(k=1;k<=inoofharmonicsanalyse;k++) {
	    EXTRAS[c].anew[k]= cos((double)k*tau)*EXTRAS[c].a[k]+sin((double)k*tau)*EXTRAS[c].b[k];
	    EXTRAS[c].bnew[k]=-sin((double)k*tau)*EXTRAS[c].a[k]+cos((double)k*tau)*EXTRAS[c].b[k];
	    EXTRAS[c].cnew[k]= cos((double)k*tau)*EXTRAS[c].c[k]+sin((double)k*tau)*EXTRAS[c].d[k];
	    EXTRAS[c].dnew[k]=-sin((double)k*tau)*EXTRAS[c].c[k]+cos((double)k*tau)*EXTRAS[c].d[k];
	  }
	  /*      //to change direction of rotation, if needed */
	     /*     //we do this by running time backwards */
		/*    //(a b) (cos(-t))=(a b)( cos(t))=(a -b)(cos(t)) */
		   /*   //(c d) (sin(-t)) (c d)(-sin(t)) (c -d)(sin(t)) */
		      if(EXTRAS[c].anew[1]*EXTRAS[c].dnew[1]-EXTRAS[c].bnew[1]*EXTRAS[c].cnew[1]<0.) {
			for(k=1;k<=inoofharmonicsanalyse;k++) {
			  EXTRAS[c].bnew[k]=-EXTRAS[c].bnew[k];
			  EXTRAS[c].dnew[k]=-EXTRAS[c].dnew[k];
			}
		      }
	  /*    // F I N D  L A M B D A S */
	     /*   //note: length of axis can only be calculated after matrix modification  */
		//tau is TEMPORAL angle to put time=0 at semimajor axis
		for(k=1;k<=inoofharmonicsanalyse;k++) {
		  tau=atan2(2.*(EXTRAS[c].a[k]*EXTRAS[c].b[k]+EXTRAS[c].c[k]*EXTRAS[c].d[k]),EXTRAS[c].a[k]*EXTRAS[c].a[k]+EXTRAS[c].c[k]*EXTRAS[c].c[k]-EXTRAS[c].b[k]*EXTRAS[c].b[k]-EXTRAS[c].d[k]*EXTRAS[c].d[k])/2.;
		  //rotate to bring semim axis to starting point
		  EXTRAS[c].anew[k]= cos(tau)*EXTRAS[c].a[k]+sin(tau)*EXTRAS[c].b[k];
		  EXTRAS[c].bnew[k]=-sin(tau)*EXTRAS[c].a[k]+cos(tau)*EXTRAS[c].b[k];
		  EXTRAS[c].cnew[k]= cos(tau)*EXTRAS[c].c[k]+sin(tau)*EXTRAS[c].d[k];
		  EXTRAS[c].dnew[k]=-sin(tau)*EXTRAS[c].c[k]+cos(tau)*EXTRAS[c].d[k];

		  //starttau is SPATIAL angle after putting time=0 at semimajor axis
		  starttau=atan2(EXTRAS[c].cnew[k],EXTRAS[c].anew[k]);
		  //angle is the angle it needs to rotate to become paralell to the x-axis
		  EXTRAS[c].angle=atan2(EXTRAS[c].cnew[1],EXTRAS[c].anew[1]);
		  
		  EXTRAS[c].lambda1[k]=sqrt(EXTRAS[c].anew[k]*EXTRAS[c].anew[k]+ EXTRAS[c].cnew[k]*EXTRAS[c].cnew[k]);
		  EXTRAS[c].lambda2[k]=sqrt(EXTRAS[c].bnew[k]*EXTRAS[c].bnew[k]+ EXTRAS[c].dnew[k]*EXTRAS[c].dnew[k]);
		  EXTRAS[c].newlambda1[k]=(EXTRAS[c].lambda1[k]+EXTRAS[c].lambda2[k])/2.;
		  EXTRAS[c].newlambda2[k]=(EXTRAS[c].lambda1[k]-EXTRAS[c].lambda2[k])/2.;
		  //  make sure it rotates in right direction
		  // lamdda1 is the largest one
		  // if you move clockwise, largest mode should be clockwise
		  // det will be newlambda1[i]^2-newlambda2[i]^2
		  // to keep rotation correct, when originally moving clockwise
		  // newlambda2[k] has to be larger than newlambda1[k]
		  if(EXTRAS[c].a[k]*EXTRAS[c].d[k]-EXTRAS[c].b[k]*EXTRAS[c].c[k]<0.) {
		    tmplambda=EXTRAS[c].newlambda1[k];
		    EXTRAS[c].newlambda1[k]=EXTRAS[c].newlambda2[k];
		    EXTRAS[c].newlambda2[k]=tmplambda;
		  }
 
		  //if(c==1)
		  // printf("%d\t%lf\n",k,starttau);
		  // printf("%d\t%lf\t%lf\t%lf\t%lf\n",k,EXTRAS[c].anew[k],EXTRAS[c].bnew[k],EXTRAS[c].cnew[k],EXTRAS[c].dnew[k]); 
		  // printf("%d\t%lf\t%lf\t%lf\t%lf\n",k,EXTRAS[c].lambda1[k],EXTRAS[c].lambda2[k],EXTRAS[c].newlambda1[k],EXTRAS[c].newlambda2[k]);
   
		  // G E T  B A C K  R I G H T  P O S I T I O N I N G  A N D  S T A R T I N G  P O I N T
		  //first, rotate SPATIALLY to get back original SPATIAL angle
		  //full code, but this can be shortened
    
		  EXTRAS[c].a1[k]= EXTRAS[c].newlambda1[k];
		  EXTRAS[c].b1[k]=0.;
		  EXTRAS[c].c1[k]=0.;
		  EXTRAS[c].d1[k]= EXTRAS[c].newlambda1[k];
		  EXTRAS[c].a2[k]= EXTRAS[c].newlambda2[k];
		  EXTRAS[c].b2[k]=0.;
		  EXTRAS[c].c2[k]=0.;
		  EXTRAS[c].d2[k]=-EXTRAS[c].newlambda2[k];

		  EXTRAS[c].arotate[k]= cos(-starttau)*EXTRAS[c].a1[k]+sin(-starttau)*EXTRAS[c].c1[k];
		  EXTRAS[c].brotate[k]= cos(-starttau)*EXTRAS[c].b1[k]+sin(-starttau)*EXTRAS[c].d1[k];
		  EXTRAS[c].crotate[k]=-sin(-starttau)*EXTRAS[c].a1[k]+cos(-starttau)*EXTRAS[c].c1[k];
		  EXTRAS[c].drotate[k]=-sin(-starttau)*EXTRAS[c].b1[k]+cos(-starttau)*EXTRAS[c].d1[k];
		  EXTRAS[c].a1[k]=EXTRAS[c].arotate[k];
		  EXTRAS[c].b1[k]=EXTRAS[c].brotate[k];
		  EXTRAS[c].c1[k]=EXTRAS[c].crotate[k];
		  EXTRAS[c].d1[k]=EXTRAS[c].drotate[k];
		  EXTRAS[c].arotate[k]= cos(-starttau)*EXTRAS[c].a2[k]+sin(-starttau)*EXTRAS[c].c2[k];
		  EXTRAS[c].brotate[k]= cos(-starttau)*EXTRAS[c].b2[k]+sin(-starttau)*EXTRAS[c].d2[k];
		  EXTRAS[c].crotate[k]=-sin(-starttau)*EXTRAS[c].a2[k]+cos(-starttau)*EXTRAS[c].c2[k];
		  EXTRAS[c].drotate[k]=-sin(-starttau)*EXTRAS[c].b2[k]+cos(-starttau)*EXTRAS[c].d2[k];
		  EXTRAS[c].a2[k]=EXTRAS[c].arotate[k];
		  EXTRAS[c].b2[k]=EXTRAS[c].brotate[k];
		  EXTRAS[c].c2[k]=EXTRAS[c].crotate[k];
		  EXTRAS[c].d2[k]=EXTRAS[c].drotate[k];
   
   
		  //at t=0 at previous starting point
		  //to get TEMPORAL starting point, bring back time to tau earlier
		  EXTRAS[c].arotate[k]= cos(-tau)*EXTRAS[c].a1[k]+sin(-tau)*EXTRAS[c].b1[k];
		  EXTRAS[c].brotate[k]=-sin(-tau)*EXTRAS[c].a1[k]+cos(-tau)*EXTRAS[c].b1[k];
		  EXTRAS[c].crotate[k]= cos(-tau)*EXTRAS[c].c1[k]+sin(-tau)*EXTRAS[c].d1[k];
		  EXTRAS[c].drotate[k]=-sin(-tau)*EXTRAS[c].c1[k]+cos(-tau)*EXTRAS[c].d1[k];
		  EXTRAS[c].a1[k]=EXTRAS[c].arotate[k];
		  EXTRAS[c].b1[k]=EXTRAS[c].brotate[k];
		  EXTRAS[c].c1[k]=EXTRAS[c].crotate[k];
		  EXTRAS[c].d1[k]=EXTRAS[c].drotate[k];
		  EXTRAS[c].arotate[k]= cos(-tau)*EXTRAS[c].a2[k]+sin(-tau)*EXTRAS[c].b2[k];
		  EXTRAS[c].brotate[k]=-sin(-tau)*EXTRAS[c].a2[k]+cos(-tau)*EXTRAS[c].b2[k];
		  EXTRAS[c].crotate[k]= cos(-tau)*EXTRAS[c].c2[k]+sin(-tau)*EXTRAS[c].d2[k];
		  EXTRAS[c].drotate[k]=-sin(-tau)*EXTRAS[c].c2[k]+cos(-tau)*EXTRAS[c].d2[k];
		  EXTRAS[c].a2[k]=EXTRAS[c].arotate[k];
		  EXTRAS[c].b2[k]=EXTRAS[c].brotate[k];
		  EXTRAS[c].c2[k]=EXTRAS[c].crotate[k];
		  EXTRAS[c].d2[k]=EXTRAS[c].drotate[k];
		}
	  //note, DC component cannot be split up in clockwise and counterclockwise contribution
	  EXTRAS[c].a1[0]=EXTRAS[c].a[0];
	  EXTRAS[c].c1[0]=EXTRAS[c].c[0];

	  
	  if(c==1){
	    printf("In Calculate L coeff a1 b1 c1 d1 newlam1 nelam2%d\n",c);
	      for(k=0;k<=inoofharmonicsanalyse;k++)
		printf("%d\t%lf\t%lf\t%lf\t%lf\t%lf\t%lf\n",k,EXTRAS[c].a1[k],EXTRAS[c].b1[k],EXTRAS[c].c1[k],EXTRAS[c].d1[k], EXTRAS[c].newlambda1[k], EXTRAS[c].newlambda2[k]);
	  }
	  
	  //determine contribution for all lobes
  //we made that the main circle always goes counterclockwise
  //we made every new1 to go counterclockwise
  //we made every new2 to go clockwise
  //so new1 gives i-1 lobes; new2 i+1;
  //so lobe p comes from new1[p+1] and new2[p-1]
  //if their starting point is 180 degree opposite, they cancel each other
  //if at the same spot, they strengthen
  //so add up vecors
  //special case 1: the core circle
    EXTRAS[c].L[1]=EXTRAS[c].newlambda1[1];
    //We divide by the overall area, to make it area-independant
    EXTRAS[c].L[1]/=EXTRAS[c].cellarea;
    
    
  //note: newlambda1[2] basically only gives a shift of the circle, I
  //think we can safely ignore it
   for(k=2;k<inoofharmonicsanalyse;k++) {
    //shortcut: do not need to calculate tau, because circles
    starttau1=atan2(EXTRAS[c].c1[k+1],EXTRAS[c].a1[k+1]);
    starttau2=atan2(EXTRAS[c].c2[k-1],EXTRAS[c].a2[k-1]);
   
  //We divide by the overall area to make it area-invariant
    EXTRAS[c].L[k]=sqrt(EXTRAS[c].newlambda1[k+1]*EXTRAS[c].newlambda1[k+1]+EXTRAS[c].newlambda2[k-1]*EXTRAS[c].newlambda2[k-1]+2.*EXTRAS[c].newlambda1[k+1]*EXTRAS[c].newlambda2[k-1]*cos(starttau1-starttau2));
    EXTRAS[c].L[k]/=EXTRAS[c].cellarea;
   
 }
	  if(c==304){
	    printf("L coeff %d\n",c);
	      for(k=1;k<=inoofharmonicsanalyse;k++){
			 // printf("L starttau1 startau2\n");
	     //fprintf(stdout,"\nmode: %d starttau1: %lf starttau2: %lf\n",k,starttau1,starttau2); 
	      //printf("%d\t%lf\t%lf\t%lf\t%lf\t%lf\n",k,EXTRAS[c].L[k],starttau1,starttau2,EXTRAS[c].newlambda1[k], EXTRAS[c].newlambda2[k]);
	  printf("%lf\n",EXTRAS[c].L[k]);
	  }
      }
	}
 	);
}



void Difference()
{
  int lobes;
  double cumulativedifference;
  CELLS(originalcells,
	if(EXTRAS[c].noofpoints) {
	  printf("xor-ing cell #%d of %d\n",c,totalcells);
	  cumulativedifference=0;
	  for(lobes=1;lobes<inoofharmonicsanalyse+2;lobes++) {
	    Xor(xor[c][lobes],original[c],reconstructed[c][lobes]);
	    //multiply by c, because reconstructed contains values c,0,c,c instead of 1,0,1,1 etc
	    difference[c][lobes]=(double)c*(double)Total(xor[c][lobes])/(double)Total(original[c]);
	    cumulativedifference+=difference[c][lobes];
	    EXTRAS[c].cumulativedifference=cumulativedifference;
	    EXTRAS[c].marginaldifference[lobes]=difference[c][lobes-1]-difference[c][lobes];
	    //printf("differnce #%d of %d\t %ft %f\n",c,totalcells,cumulativedifference,EXTRAS[c].cumulativedifference);
	  }
	
	);

}
}

void Entropy() //Taking the L landscape
{
  int lobes;
  //double temp;
  
  CELLS(reconstructedcells,
  if(EXTRAS[c].noofpoints) {
   for(lobes=1;lobes<=inoofharmonicsanalyse;lobes++) {
	  EXTRAS[c].totalproportion+=(double)EXTRAS[c].L[lobes];
    }
    for(lobes=1;lobes<inoofharmonicsanalyse;lobes++) {
	  EXTRAS[c].proportion[lobes]=((double)EXTRAS[c].L[lobes]/(double)EXTRAS[c].totalproportion);
	  EXTRAS[c].entropy+=-((double)EXTRAS[c].proportion[lobes]*(double)log(EXTRAS[c].proportion[lobes]));
	 
  }
 //printf("%f\n",EXTRAS[c].entropy); 
}
     
  );
}


void AsignCellProperties(int ac,char *av[])
{
	 //From displaycellproperties_02.c:
  //int i;
 int nrow,ncol,dummynrow,dummyncol;
 int k;
  
   //what is segmented_cells at t=1?
  if(snprintf(readcells,STRING,"%s",av[5])>=STRING) {
    fprintf(stderr,"warning: segmented cells at t=1 name too long: %s\n",av[5]);
    exit(EXIT_FAILURE);
  }
  
      //what is original_image?
  if(snprintf(readimage,STRING,"%s",av[3])>=STRING) {
    fprintf(stderr,"warning: orginal image name too long: %s\n",av[3]);
    exit(EXIT_FAILURE);
  }
  
 
  //the cells
  ColorName(CELLWALL,CELLWALL,"black");
  ColorName(PAVEMENTCELL,PAVEMENTCELL,"green");
  ColorName(STOMATA,STOMATA,"red");
  ColorName(255,255,"pink");
     
  if(ReadSizePNG(&nrow,&ncol,readcells)) {
    fprintf(stderr,"warning: image file \"%s\" could not be opened!\n",readcells);
    exit(EXIT_FAILURE);
  } 
  
  if(ReadSizePNG(&dummynrow,&dummyncol,readimage)) {
    fprintf(stderr,"warning: image file \"%s\" could not be opened!\n",readimage);
    exit(EXIT_FAILURE);
  } 
  
  
  if((nrow!=dummynrow) || (ncol!=dummyncol)) {
    fprintf(stderr,"warning: the image and the cell reconstruction are of different sizes, check your files!\n");
    exit(EXIT_FAILURE);
  }
  printf("ncol %d, nro2 %d",ncol,nrow);
  imageheight=nrow;
  imagewidth=ncol;
 
      //Find the max sigma from oldsigma
  CELLS(originalcells,
   if(EXTRAS[c].noofpoints){
	   maximumsigma=EXTRAS[c].oldsigma;
	   if(EXTRAS[c].oldsigma>maximumsigma)
	    maximumsigma=EXTRAS[c].oldsigma;
	    maximumsigma=maximumsigma+1;
  }
  );
  
  state_displaycellproperties=New();
  image_displaycellproperties=New();
  state_oldsigma=New();
 
  CELLS(originalcells,
  if(EXTRAS[c].noofpoints){
	  c=EXTRAS[c].oldsigma;
  }
	  );
	     
  ReadPatPNG(state_displaycellproperties,1,1,readcells,10000);
  ReadPatPNG(image_displaycellproperties,1,1,readimage,maximumsigma+1000);
  UpdateCFill(state,&cells);
  UpdateCFill(state_oldsigma,&originalcells);
    
  CELLS(cells,
	if(c>specialcelltype){
	  cells.celltype[c]=PAVEMENTCELL;
	//if(c==location)
	  //cells.celltype[c]=STOMATA;
  }
	else{
	  cells.celltype[c]=CELLWALL;
  }
	);
	
  InitCellPosition(&originalcells);
  //InitCellPosition(&cells);
  //maxdistance=2;
  //UpdateCellPosition(state_oldsigma,&originalcells); 
  //UpdateCellPosition(state_displaycellproperties,&originalcells); 
  // UpdateCellNeighbours(state_displaycellproperties,&originalcells); 
  
  UpdateCellShape(&originalcells);
  //UpdateCellShape(&cells);
   
  PLANE(
    
    k=state[i][j];
    
    CELLS(originalcells,
	if(EXTRAS[c].noofpoints) {		 
    if (state[i][j]==EXTRAS[c].oldsigma){
		k=c;
    }
    }
	);
	);
	  
 OpenDisplay("Cells",imagewidth,2*imageheight);
 
  do {
   //CellDisplay(state_displaycellproperties,&cells,0,0,0);
   //CPlaneDisplay(image_displaycellproperties,state_displaycellproperties,0,imageheight,10000+maximumsigma);
   //PlaneDisplay(image_displaycellproperties,0,0,0);
   PlaneDisplay(image_displaycellproperties,0,imageheight,1000+maximumsigma);
   usleep(10000);
  }while(!CheckDisplay());
 
}


void Findyourcell()
{
//int k=1;
//int g=0;
double **squaredistance, **minimumsquare;
int noofcellst00=0;
int noofcellst01=0;
int lobes;
int noofcellst0=0;
int noofcellst1=0;
int i; int j;

 CELLS(reconstructedcells,;
	if(EXTRAS[c].noofpoints) {
		//printf("c=%d\t t=%d\n",c, EXTRAS[c].timepoint);
    if(EXTRAS[c].timepoint==0) noofcellst00++;  //number of cells in image at t=0
    if(EXTRAS[c].timepoint==1) noofcellst01++; // number of cells in image at t=1
    }
	);
	printf("noofcells t0=%d\t noofcells t1=%d\t totalcells%d\n",noofcellst00,noofcellst01,totalcells);
   
   //Allocate memory for a two-dimensional array
    squaredistance = malloc(noofcellst00 * sizeof(double *));
    minimumsquare = malloc(noofcellst00 * sizeof(double *));
    
     if(squaredistance == NULL || minimumsquare == NULL)
     {
		fprintf(stderr, "out of memory\n");
		exit(EXIT_FAILURE);
		}
	for(i = 0; i <= noofcellst00; i++)
		{
		squaredistance[i] = malloc(noofcellst01 * sizeof(double));
		minimumsquare[i] = malloc(noofcellst01 * sizeof(double));
		if(squaredistance[i] == NULL || minimumsquare == NULL)
			{
			fprintf(stderr, "out of memory\n");
			exit(EXIT_FAILURE);
			}
	  }
	  //Make sure everything is 0.
	  	for (i = 0; i <= noofcellst00; i++){
			for(j = 0; j <= noofcellst01; j++)
			squaredistance[i][j]=0;
			minimumsquare[i][j]=0;
		    }
//for(j = 1; j <= noofcellst01; j++)
		//{
		//squaredistance[i][j] = malloc(inoofharmonicsanalyse * sizeof(double));
		//if(squaredistance[i][j] == NULL)
			//{
			//fprintf(stderr, "out of memory\n");
			//exit(EXIT_FAILURE);
			//}

  
  CELLS(reconstructedcells,
	if(EXTRAS[c].noofpoints) {	
	for(lobes=1;lobes<=inoofharmonicsanalyse;lobes++){
		for (noofcellst0=1;noofcellst0<=noofcellst00; noofcellst0++){
			for (noofcellst1=1;noofcellst1<=noofcellst01; noofcellst1++){
		squaredistance[noofcellst0][noofcellst1]+=(double)((EXTRAS[noofcellst0].L[lobes]-EXTRAS[noofcellst1+noofcellst00].L[lobes])*(EXTRAS[noofcellst0].L[lobes]-EXTRAS[noofcellst1+noofcellst00].L[lobes]));	
    }}}  
  } 
  );
   for (noofcellst0=1;noofcellst0<=noofcellst00; noofcellst0++){
			for (noofcellst1=1;noofcellst1<=noofcellst01; noofcellst1++){
    printf("squaredistance of %d and %d is %f\n",noofcellst0,noofcellst1+noofcellst00, squaredistance[noofcellst0][noofcellst1]);
             }
    }

//Find the cell that resemble the most.
	
    min=squaredistance[1][1];
    
    for (i=2; i < noofcellst01 ; i++){
		if (squaredistance[1][i] < min)
		{
			min=squaredistance[1][i];
			location = i+1;
		}
	}
 printf("The cell that resemble the most is %d, and the square of the difference is %f.\n", location, min);

 CELLS(originalcells,
	if(EXTRAS[c].noofpoints && c==location) {
 printf("And the oldsigma is %d\n", EXTRAS[location].oldsigma);
}
);
}

int main(int argc,char *argv[])
{
  char a_string[STRING];
 // int k=1,lobe=1;
  //int lobes;
  //FILE *fp;
   
  mouse=&Mouse;
  keyboard=&Key;
  scale=2;

  //read the data from file
  ReadData(argc,argv);

  //draw the segmented cell adges into the planes 
  FillOriginalDataPlanes();
  //calculate the modes of the EFA
  CalculateReconstruction();
  //calculate the lobe-coefficients
  CalculateLcoefficients();
   
  //draw the reconstructed cell edges for each lobe number
  DetermineReconstructedShape();

  //fill up the cells 
  FillOriginalShape();
  FillReconstructedShape();

  //calculate the XOR
  Difference();
  
//calculate entropy values
  Entropy();
 
 //snprintf(a_string,STRING,"cell=%d; time=%d; lobe=%d; original sigma=%d",EXTRAS[1].cellnumber,EXTRAS[1].timepoint,lobe,EXTRAS[1].oldsigma);
 
 Findyourcell();
 
//Display a plane with the cell resembling the most
 AsignCellProperties(argc,argv);
 
 //snprintf(a_string,STRING,"Cells");
 //OpenDisplay(a_string,imagewidth,2*imageheight);
 
  //do {
   ////CellDisplay(state_displaycellproperties,&cells,0,0,0);
   ////CPlaneDisplay(image_displaycellproperties,state_displaycellproperties,0,imageheight,10000+maximumsigma);
   //PlaneDisplay(image_displaycellproperties,0,imageheight,10000+maximumsigma);
   //usleep(10000);
  //}while(!CheckDisplay());
  
  
 //snprintf(a_string,STRING,"Cells");
 //OpenDisplay(a_string,imagewidth,imageheight);
 
  //do {
   //CellDisplay(state_displaycellproperties,&originalcells,0,0,0);
   ////CPlaneDisplay(image_displaycellproperties,state,0,ncol,10000+maximumsigma);
    //usleep(10000);
  //}while(!CheckDisplay());
 

   printf("\t...done.\n");
  return 0;
}
