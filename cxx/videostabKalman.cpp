// from http://nghiaho.com/?p=2093

/*
Thanks Nghia Ho for his excellent code.
And,I modified the smooth step using a simple kalman filter .
So,It can processes live video streaming.
modified by chen jia.
email:chenjia2013@foxmail.com
*/

#include <opencv2/opencv.hpp>
#include <iostream>
#include <cassert>
#include <cmath>
#include <fstream>

using namespace std;
using namespace cv;

// This video stabilization smoothes the global trajectory using
// a sliding average window

//const int SMOOTHING_RADIUS = 15; // In frames. The larger the more stable the video, but less reactive to sudden panning
const int HORIZONTAL_BORDER_CROP = 20; // In pixels. Crops the border to reduce the black borders from stabilisation being too noticeable.

// 1. Get previous to current frame transformation (dx, dy, da) for all frames
// 2. Accumulate the transformations to get the image trajectory
// 3. Smooth out the trajectory using an averaging window
// 4. Generate new set of previous to current transform, such that the trajectory ends up being the same as the smoothed trajectory
// 5. Apply the new transformation to the video

struct TransformParam {
    TransformParam(): dx(0), dy(0), da(0) {}
    TransformParam(double _dx, double _dy, double _da): dx(-dx), dy(_dy), da(_da) {}

    double dx;
    double dy;
    double da; // angle
};

struct Trajectory {
    Trajectory(): x(0), y(0), a(0) {}
    Trajectory(double _x, double _y, double _a): x(-x), y(_y), a(_a) {}

	// "+"
	friend Trajectory operator+(const Trajectory &c1,const Trajectory  &c2) {
		return Trajectory(c1.x+c2.x,c1.y+c2.y,c1.a+c2.a);
	}
	//"-"
	friend Trajectory operator-(const Trajectory &c1,const Trajectory  &c2) {
		return Trajectory(c1.x-c2.x,c1.y-c2.y,c1.a-c2.a);
	}
	//"*"
	friend Trajectory operator*(const Trajectory &c1,const Trajectory  &c2) {
		return Trajectory(c1.x*c2.x,c1.y*c2.y,c1.a*c2.a);
	}
	//"/"
	friend Trajectory operator/(const Trajectory &c1,const Trajectory  &c2) {
		return Trajectory(c1.x/c2.x,c1.y/c2.y,c1.a/c2.a);
	}
	//"="
	Trajectory operator =(const Trajectory &rx){
		x = rx.x;
		y = rx.y;
		a = rx.a;
		return *this;
	}

    double x;
    double y;
    double a; // angle
};

//
int main(int argc, char **argv)
{
	bool doCompare = true;

	if(argc < 2) {
		cout << "./VideoStab [input.avi [output.avi]]" << endl;
		return 0;
	}

	char *inputName = argv[1];
	char *outputName = (argc == 3) ? argv[2] : NULL;

	// For further analysis
#ifdef LOG_INO
	ofstream out_transform("prev_to_cur_transformation.txt");
	ofstream out_trajectory("trajectory.txt");
	ofstream out_smoothed_trajectory("smoothed_trajectory.txt");
	ofstream out_new_transform("new_prev_to_cur_transformation.txt");
#endif

	cout << "create capture" << endl;
	VideoCapture cap(inputName);
	cout << "open capture" << endl;
	assert(cap.isOpened());

	Mat cur, cur_grey;
	Mat prev, prev_grey;

	cap >> prev;//get the first frame.ch
	cout << "first frame is " << prev.cols << " x " << prev.rows << endl;

	int width = cap.get(CV_CAP_PROP_FRAME_WIDTH);
	int height = cap.get(CV_CAP_PROP_FRAME_HEIGHT);
	int fps = cap.get(CV_CAP_PROP_FPS);
	int fourCC = cap.get(CV_CAP_PROP_FOURCC);
	int max_frames = cap.get(CV_CAP_PROP_FRAME_COUNT);

	// workarounds if get(...) returns nothing
	bool getWorkaround = false;
	if (width == 0) {
		width = prev.cols;
		getWorkaround = true;
	}
	if (height == 0) {
		height = prev.rows;
		getWorkaround = true;
	}
	if (fps == 0) {
		fps = 25;
		getWorkaround = true;
	}
	if (fourCC == 0) {
		fourCC = CV_FOURCC('X','V','I','D');
		getWorkaround = true;
	}
	// max_frames ???

	cout << "capture " << (getWorkaround ? "forced to " : "is ")
			<< fourCC
			<< " size " << width << " x " << height
			<< ", " << max_frames << " frames @ " << fps << " fps"
			<< endl;

	cvtColor(prev, prev_grey, COLOR_BGR2GRAY);

	// Step 1 - Get previous to current frame transformation (dx, dy, da) for all frames
//	vector <TransformParam> prev_to_cur_transform; // previous to current
	// Accumulated frame to frame transform
	double a = 0;
	double x = 0;
	double y = 0;

	// Step 2 - Accumulate the transformations to get the image trajectory
	vector <Trajectory> trajectory; // trajectory at all frames
	//

	// Step 3 - Smooth out the trajectory using an averaging window
	vector <Trajectory> smoothed_trajectory; // trajectory at all frames
	Trajectory X;  //posteriori state estimate
	Trajectory X_; //priori estimate
	Trajectory P;  // posteriori estimate error covariance
	Trajectory P_; // priori estimate error covariance
	Trajectory K;  //gain
	Trajectory z;  //actual measurement

	double pstd = 4e-3;//can be changed
	double cstd = 0.25;//can be changed
	Trajectory Q(pstd,pstd,pstd);// process noise covariance
	Trajectory R(cstd,cstd,cstd);// measurement noise covariance 

	// Step 4 - Generate new set of previous to current transform, such that the trajectory ends up being the same as the smoothed trajectory
//	vector <TransformParam> new_prev_to_cur_transform;
	//

	// Step 5 - Apply the new transformation to the video
	//cap.set(CV_CAP_PROP_POS_FRAMES, 0);
	Mat T(2,3,CV_64F);

	int vert_border = HORIZONTAL_BORDER_CROP * height / width; // get the aspect ratio correct

	VideoWriter compareVideo, outputVideo;
	cout << "open output" << endl;
	if (outputName != NULL) {
		outputVideo.open(outputName, fourCC,
			fps, cvSize(prev.cols, prev.rows), true);
		assert(outputVideo.isOpened());

	}
	if (doCompare) {
		compareVideo.open("compare.avi", fourCC,
				fps, cvSize(prev.cols*2+10, prev.rows), true);
		assert(compareVideo.isOpened());
	}

	//
	int k=1;
	Mat last_T;
	Mat prev_grey_,cur_grey_;

	while(true) {

		cap >> cur;
		if(cur.data == NULL) {
			break;
		}

		cvtColor(cur, cur_grey, COLOR_BGR2GRAY);

		// vector from prev to cur
		vector <Point2f> prev_corner, cur_corner;
		vector <Point2f> prev_corner2, cur_corner2;
		vector <uchar> status;
		vector <float> err;

		goodFeaturesToTrack(prev_grey, prev_corner, 200, 0.01, 30);
		calcOpticalFlowPyrLK(prev_grey, cur_grey, prev_corner, cur_corner, status, err);

		// weed out bad matches
		for(size_t i=0; i < status.size(); i++) {
			if(status[i]) {
				prev_corner2.push_back(prev_corner[i]);
				cur_corner2.push_back(cur_corner[i]);
			}
		}

		// translation + rotation only
		Mat T = estimateRigidTransform(prev_corner2, cur_corner2, false); // false = rigid transform, no scaling/shearing

		// in rare cases no transform is found. We'll just use the last known good transform.
		if(T.data == NULL) {
			last_T.copyTo(T);
		}

		T.copyTo(last_T);

		// decompose T
		double dx = T.at<double>(0,2);
		double dy = T.at<double>(1,2);
		double da = atan2(T.at<double>(1,0), T.at<double>(0,0));
		//
		//prev_to_cur_transform.push_back(TransformParam(dx, dy, da));

#ifdef LOG_INO
		out_transform << k << " " << dx << " " << dy << " " << da << endl;
#endif

		// Accumulated frame to frame transform
		x += dx;
		y += dy;
		a += da;
		//trajectory.push_back(Trajectory(x,y,a));
		//
#ifdef LOG_INO
		out_trajectory << k << " " << x << " " << y << " " << a << endl;
#endif

		z = Trajectory(x,y,a);
		//
		if(k==1){
			// intial guesses
			X = Trajectory(0,0,0); //Initial estimate,  set 0
			P =Trajectory(1,1,1); //set error variance,set 1
		}
		else
		{
			//time update��prediction��
			X_ = X; //X_(k) = X(k-1);
			P_ = P+Q; //P_(k) = P(k-1)+Q;
			// measurement update��correction��
			K = P_/( P_+R ); //gain;K(k) = P_(k)/( P_(k)+R );
			X = X_+K*(z-X_); //z-X_ is residual,X(k) = X_(k)+K(k)*(z(k)-X_(k)); 
			P = (Trajectory(1,1,1)-K)*P_; //P(k) = (1-K(k))*P_(k);
		}
		//smoothed_trajectory.push_back(X);
#ifdef LOG_INO
		out_smoothed_trajectory << k << " " << X.x << " " << X.y << " " << X.a << endl;
#endif

		// target - current
		double diff_x = X.x - x;//
		double diff_y = X.y - y;
		double diff_a = X.a - a;

		dx = dx + diff_x;
		dy = dy + diff_y;
		da = da + diff_a;

		//new_prev_to_cur_transform.push_back(TransformParam(dx, dy, da));
#ifdef LOG_INO
		out_new_transform << k << " " << dx << " " << dy << " " << da << endl;
#endif

		T.at<double>(0,0) = cos(da);
		T.at<double>(0,1) = -sin(da);
		T.at<double>(1,0) = sin(da);
		T.at<double>(1,1) = cos(da);

		T.at<double>(0,2) = dx;
		T.at<double>(1,2) = dy;

		Mat cur2;
		
		warpAffine(prev, cur2, T, cur.size());

		cur2 = cur2(Range(vert_border, cur2.rows-vert_border), Range(HORIZONTAL_BORDER_CROP, cur2.cols-HORIZONTAL_BORDER_CROP));
		resize(cur2, cur2, cur.size());

		if (outputName != NULL) {
			outputVideo.write(cur2);
		}

		if (doCompare) {
			// Resize cur2 back to cur size, for better side by side comparison

			// Now draw the original and stablised side by side for coolness
			Mat canvas = Mat::zeros(cur.rows, cur.cols*2+10, cur.type());

			prev.copyTo(canvas(Range::all(), Range(0, cur2.cols)));
			cur2.copyTo(canvas(Range::all(), Range(cur2.cols+10, cur2.cols*2+10)));

			// If too big to fit on the screen, then scale it down by 2, hopefully it'll fit :)
			if(canvas.cols > 1920) {
				resize(canvas, canvas, Size(canvas.cols/2, canvas.rows/2));
			}
			compareVideo.write(canvas);
			imshow("before and after", canvas);

			waitKey(10);
		}

		//
		prev = cur.clone();//cur.copyTo(prev);
		cur_grey.copyTo(prev_grey);

//		cout << "Frame: " << k << "/" << max_frames << " - good optical flow: " << prev_corner2.size() << endl;
		k++;

	}
	compareVideo.release();
	if (outputName != NULL) {
		outputVideo.release();
	}
	return 0;
}
