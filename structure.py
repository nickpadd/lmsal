import warnings
warnings.filterwarnings("ignore", message = "divide by zero encountered in log")
warnings.filterwarnings("ignore", message = "From scipy 0.13.0, the output shape of")
warnings.filterwarnings("ignore", message = "invalid value encountered in greater")
warnings.filterwarnings("ignore", message = "invalid value encountered in less")
warnings.filterwarnings("ignore", message = "invalid value encountered in log")
warnings.filterwarnings("ignore", message = "invalid value encountered in multiply")
warnings.filterwarnings("ignore", message = "numpy.dtype size changed")

from IPython.core import debugger; debug = debugger.Pdb().set_trace
from matplotlib.colors import LogNorm
from matplotlib.path import Path
from os import listdir
from os.path import isfile, join
from PIL import Image, ImageEnhance
from recorder import Recorder
from scipy import ndimage
from scipy.stats import iqr
from skimage import feature
from skimage import measure
from sunpy.io import read_file_header
from sunpy.map import Map
from timeit import default_timer as timer
from tqdm import tqdm
import argparse
import astropy.units as u
import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
import os

RECORDER = Recorder()
RECORDER.display_start_time("structure")

parser = argparse.ArgumentParser()
parser.add_argument("--cleardirs", nargs = "?", const = True, type = bool)
args = parser.parse_args()

RECORDER.sys_text("Importing data directories")
SAVEPATH = "data/outputs/"
PATH94 = "data/AIA94/"; PATH131 = "data/AIA131/"; PATH171 = "data/AIA171/"; PATH193 = "data/AIA193/"; PATH211 = "data/AIA211/"; PATH304 = "data/AIA304/"; PATH335 = "data/AIA335/"

DIR94 = [f for f in listdir(PATH94) if isfile(join(PATH94, f))]; DIR94.sort()
DIR131 = [f for f in listdir(PATH131) if isfile(join(PATH131, f))]; DIR131.sort()
DIR171 = [f for f in listdir(PATH171) if isfile(join(PATH171, f))]; DIR171.sort()
DIR193 = [f for f in listdir(PATH193) if isfile(join(PATH193, f))]; DIR193.sort()
DIR211 = [f for f in listdir(PATH211) if isfile(join(PATH211, f))]; DIR211.sort()
DIR304 = [f for f in listdir(PATH304) if isfile(join(PATH304, f))]; DIR304.sort()
DIR335 = [f for f in listdir(PATH335) if isfile(join(PATH335, f))]; DIR335.sort()

if DIR94[0] == ".DS_Store":
	DIR94 = DIR94[1:]
if DIR131[0] == ".DS_Store":
	DIR131 = DIR131[1:]
if DIR171[0] == ".DS_Store":
	DIR171 = DIR171[1:]
if DIR193[0] == ".DS_Store":
	DIR193 = DIR193[1:]
if DIR211[0] == ".DS_Store":
	DIR211 = DIR211[1:]
if DIR304[0] == ".DS_Store":
	DIR304 = DIR304[1:]
if DIR335[0] == ".DS_Store":
	DIR335 = DIR335[1:]

K94 = []; t94 = []
K131 = []; t131 = []
K171 = []; t171 = []
K193 = []; t193 = []
K211 = []; t211 = []
K304 = []; t304 = []
K335 = []; t335 = []

if args.cleardirs:
	RECORDER.sys_text("Clearing image directories")
	os.system("rm %sraw/AIA94/*" % SAVEPATH); os.system("rm %senhanced/AIA94/*" % SAVEPATH); os.system("rm %sedge/AIA94/*" % SAVEPATH); os.system("rm %sbinary/AIA94/*" % SAVEPATH)
	os.system("rm %sraw/AIA131/*" % SAVEPATH); os.system("rm %senhanced/AIA131/*" % SAVEPATH); os.system("rm %sedge/AIA131/*" % SAVEPATH); os.system("rm %sbinary/AIA131/*" % SAVEPATH)
	os.system("rm %sraw/AIA171/*" % SAVEPATH); os.system("rm %senhanced/AIA171/*" % SAVEPATH); os.system("rm %sedge/AIA171/*" % SAVEPATH); os.system("rm %sbinary/AIA171/*" % SAVEPATH)
	os.system("rm %sraw/AIA193/*" % SAVEPATH); os.system("rm %senhanced/AIA193/*" % SAVEPATH); os.system("rm %sedge/AIA193/*" % SAVEPATH); os.system("rm %sbinary/AIA193/*" % SAVEPATH)
	os.system("rm %sraw/AIA211/*" % SAVEPATH); os.system("rm %senhanced/AIA211/*" % SAVEPATH); os.system("rm %sedge/AIA211/*" % SAVEPATH); os.system("rm %sbinary/AIA211/*" % SAVEPATH)
	os.system("rm %sraw/AIA304/*" % SAVEPATH); os.system("rm %senhanced/AIA304/*" % SAVEPATH); os.system("rm %sedge/AIA304/*" % SAVEPATH); os.system("rm %sbinary/AIA304/*" % SAVEPATH)
	os.system("rm %sraw/AIA335/*" % SAVEPATH); os.system("rm %senhanced/AIA335/*" % SAVEPATH); os.system("rm %sedge/AIA335/*" % SAVEPATH); os.system("rm %sbinary/AIA335/*" % SAVEPATH)
	RECORDER.sys_text("Image directories cleared")

def print_raw_info(fits):
	tqdm.write("\t\t\t%s %s %d" % (fits.observatory, fits.detector, int(fits.measurement.value)))
	tqdm.write("\t\t\tDatetime:\t%s" % (fits.date))
	tqdm.write("\t\t\tExposure time:\t%s s" % (fits.exposure_time.value))
	tqdm.write("\t\t\tLocation:\t(%d, %d) arcsec" % ((fits.top_right_coord.Tx.value + fits.bottom_left_coord.Tx.value) / 2, (fits.top_right_coord.Ty.value + fits.bottom_left_coord.Ty.value) / 2))
	tqdm.write("\t\t\tMed val:\t%.3f" % (np.median(fits.data)))

def print_sdata(sx, sy, e):
	sx = sx.round(decimals = 1)
	sy = sy.round(decimals = 1)
	e = e.round(decimals = 1)
	tqdm.write("\n*** sobel_x ***")
	tqdm.write("%s" % sx)
	tqdm.write("\n*** sobel_y ***")
	tqdm.write("%s" % sy)
	tqdm.write("\n*** sobel_hypot ***")
	tqdm.write("%s" % e)
	tqdm.write("\t\t\tMed sobel_hypot val:\t%.3f" % (np.median(e)))
	tqdm.write("\t\t\t" + "*** " * 11)

def gen_bin_img(temp_im):
	ie_sharp = ImageEnhance.Sharpness(temp_im)
	proc_im = ie_sharp.enhance(4)
	ie_contr = ImageEnhance.Contrast(proc_im)
	proc_im = ie_contr.enhance(1.6)
	ie_bright = ImageEnhance.Brightness(proc_im)
	proc_im = ie_bright.enhance(0.3)
	ie_contr = ImageEnhance.Contrast(proc_im)
	proc_im = ie_contr.enhance(2)
	gr = np.dot(np.asarray(proc_im)[...,:3], [0.2989, 0.5870, 0.1140])
	return gr

##### ----- #####
N = 3 #len(DIR94)
##### ----- #####

for K in tqdm(range(N), desc = "Generating raw images"):
	temp = Map(PATH94 + DIR94[K])
	RECORDER.info_text("|===================== Processing datetime %s (#%d) =====================|" % (temp.date, K))
	K94.append([temp.data, temp.exposure_time.value, temp.date, read_file_header(PATH94 + DIR94[K])[1]])
	print_raw_info(temp)
	tempdata = K94[-1][0] / K94[-1][1]
	tempheader = K94[-1][3]
	temp = Map((tempdata, tempheader))
	temp.raw_img(K, SAVEPATH + "raw/AIA94", 250)
	RECORDER.info_text("Raw AIA94 image data saved")

	temp = Map(PATH131 + DIR131[K])
	K131.append([temp.data, temp.exposure_time.value, temp.date, read_file_header(PATH131 + DIR131[K])[1]])
	print_raw_info(temp)
	tempdata = K131[-1][0] / K131[-1][1]
	tempheader = K131[-1][3]
	temp = Map((tempdata, tempheader))
	temp.raw_img(K, SAVEPATH + "raw/AIA131", 250)
	RECORDER.info_text("Raw AIA131 image data saved")

	temp = Map(PATH171 + DIR171[K])
	K171.append([temp.data, temp.exposure_time.value, temp.date, read_file_header(PATH171 + DIR171[K])[1]])
	print_raw_info(temp)
	tempdata = K171[-1][0] / K171[-1][1]
	tempheader = K171[-1][3]
	temp = Map((tempdata, tempheader))
	temp.raw_img(K, SAVEPATH + "raw/AIA171", 250)
	RECORDER.info_text("Raw AIA171 image data saved")

	temp = Map(PATH193 + DIR193[K])
	K193.append([temp.data, temp.exposure_time.value, temp.date, read_file_header(PATH193 + DIR193[K])[1]])
	print_raw_info(temp)
	tempdata = K193[-1][0] / K193[-1][1]
	tempheader = K193[-1][3]
	temp = Map((tempdata, tempheader))
	temp.raw_img(K, SAVEPATH + "raw/AIA193", 250)
	RECORDER.info_text("Raw AIA193 image data saved")

	temp = Map(PATH211 + DIR211[K])
	K211.append([temp.data, temp.exposure_time.value, temp.date, read_file_header(PATH211 + DIR211[K])[1]])
	print_raw_info(temp)
	tempdata = K211[-1][0] / K211[-1][1]
	tempheader = K211[-1][3]
	temp = Map((tempdata, tempheader))
	temp.raw_img(K, SAVEPATH + "raw/AIA211", 250)
	RECORDER.info_text("Raw AIA211 image data saved")

	temp = Map(PATH304 + DIR304[K])
	K304.append([temp.data, temp.exposure_time.value, temp.date, read_file_header(PATH304 + DIR304[K])[1]])
	print_raw_info(temp)
	tempdata = K304[-1][0] / K304[-1][1]
	tempheader = K304[-1][3]
	temp = Map((tempdata, tempheader))
	temp.raw_img(K, SAVEPATH + "raw/AIA304", 250)
	RECORDER.info_text("Raw AIA304 image data saved")

	temp = Map(PATH335 + DIR335[K])
	K335.append([temp.data, temp.exposure_time.value, temp.date, read_file_header(PATH335 + DIR335[K])[1]])
	print_raw_info(temp)
	tempdata = K335[-1][0] / K335[-1][1]
	tempheader = K335[-1][3]
	temp = Map((tempdata, tempheader))
	temp.raw_img(K, SAVEPATH + "raw/AIA335", 250)
	RECORDER.info_text("Raw AIA335 image data saved")

for K in tqdm(range(N), desc = "Correcting for exposure time"):
	temp = Image.open("%sraw/AIA94/raw_%04d.png" % (SAVEPATH, K))
	ar = np.asarray(temp)
	new = np.dot(ar[...,:3], [0.2989, 0.5870, 0.1140])
	new /= K94[K][1]
	plt.imsave("%sraw/AIA94/-raw_%04d.png" % (SAVEPATH, K), new, cmap = "sdoaia94", vmin = 0, vmax = 100)

debug()

for K in tqdm(range(N), desc = "Generating intensity distribution"):
	if K94[K][1] > 0:
		t94 = np.append(t94, np.median(K94[K][0] / K94[K][1]))
	if K131[K][1] > 0:
		t131 = np.append(t131, np.median(K131[K][0] / K131[K][1]))
	if K171[K][1] > 0:
		t171 = np.append(t171, np.median(K171[K][0] / K171[K][1]))
	if K193[K][1] > 0:
		t193 = np.append(t193, np.median(K193[K][0] / K193[K][1]))
	if K211[K][1] > 0:
		t211 = np.append(t211, np.median(K211[K][0] / K211[K][1]))
	if K304[K][1] > 0:
		t304 = np.append(t304, np.median(K304[K][0] / K304[K][1]))
	if K335[K][1] > 0:
		t335 = np.append(t335, np.median(K335[K][0] / K335[K][1]))

MED94 = np.median(t94); IQR94 = iqr(t94)
MED131 = np.median(t131); IQR131 = iqr(t131)
MED171 = np.median(t171); IQR171 = iqr(t171)
MED193 = np.median(t193); IQR193 = iqr(t193)
MED211 = np.median(t211); IQR211 = iqr(t211)
MED304 = np.median(t304); IQR304 = iqr(t304)
MED335 = np.median(t335); IQR335 = iqr(t335)

meds = [MED94, MED131, MED171, MED193, MED211, MED304, MED335]
iqrs = [IQR94, IQR131, IQR171, IQR193, IQR211, IQR304, IQR335]

print "\t\t\t*********************"
print "\t\t\tID\tMED\tIQR"
print "\t\t\t94\t%.3f\t%.3f" % (MED94, IQR94)
print "\t\t\t131\t%.3f\t%.3f" % (MED131, IQR131)
print "\t\t\t171\t%.3f\t%.3f" % (MED171, IQR171)
print "\t\t\t193\t%.3f\t%.3f" % (MED193, IQR193)
print "\t\t\t211\t%.3f\t%.3f" % (MED211, IQR211)
print "\t\t\t304\t%.3f\t%.3f" % (MED304, IQR304)
print "\t\t\t335\t%.3f\t%.3f" % (MED335, IQR335)
print "\t\t\t*********************"

for K in tqdm(range(N), desc = "Generating enhanced images"):
	RECORDER.info_text("|===================== Processing datetime %s (#%d) =====================|" % (K94[K][2], K))
	tempdata = K94[K][0] / K94[K][1]
	tempheader = K94[K][3]
	sx = ndimage.sobel(tempdata, axis = 0, mode = "constant")
	sy = ndimage.sobel(tempdata, axis = 1, mode = "constant")
	e = np.hypot(sx, sy)
	print_sdata(sx, sy, e)
	temp = Map((e, tempheader))
	temp.e_img(K, SAVEPATH + "enhanced/AIA94", 250)
	RECORDER.info_text("Enhanced AIA94 image data saved")

	tempdata = K131[K][0] / K131[K][1]
	tempheader = K131[K][3]
	sx = ndimage.sobel(tempdata, axis = 0, mode = "constant")
	sy = ndimage.sobel(tempdata, axis = 1, mode = "constant")
	e = np.hypot(sx, sy)
	print_sdata(sx, sy, e)
	temp = Map((e, tempheader))
	temp.e_img(K, SAVEPATH + "enhanced/AIA131", 250)
	RECORDER.info_text("Enhanced AIA131 image data saved")

	tempdata = K171[K][0] / K171[K][1]
	tempheader = K171[K][3]
	sx = ndimage.sobel(tempdata, axis = 0, mode = "constant")
	sy = ndimage.sobel(tempdata, axis = 1, mode = "constant")
	e = np.hypot(sx, sy)
	print_sdata(sx, sy, e)
	temp = Map((e, tempheader))
	temp.e_img(K, SAVEPATH + "enhanced/AIA171", 250)
	RECORDER.info_text("Enhanced AIA171 image data saved")

	tempdata = K193[K][0] / K193[K][1]
	tempheader = K193[K][3]
	sx = ndimage.sobel(tempdata, axis = 0, mode = "constant")
	sy = ndimage.sobel(tempdata, axis = 1, mode = "constant")
	e = np.hypot(sx, sy)
	print_sdata(sx, sy, e)
	temp = Map((e, tempheader))
	temp.e_img(K, SAVEPATH + "enhanced/AIA193", 250)
	RECORDER.info_text("Enhanced AIA193 image data saved")

	tempdata = K211[K][0] / K211[K][1]
	tempheader = K211[K][3]
	sx = ndimage.sobel(tempdata, axis = 0, mode = "constant")
	sy = ndimage.sobel(tempdata, axis = 1, mode = "constant")
	e = np.hypot(sx, sy)
	print_sdata(sx, sy, e)
	temp = Map((e, tempheader))
	temp.e_img(K, SAVEPATH + "enhanced/AIA211", 250)
	RECORDER.info_text("Enhanced AIA211 image data saved")

	tempdata = K304[K][0] / K304[K][1]
	tempheader = K304[K][3]
	sx = ndimage.sobel(tempdata, axis = 0, mode = "constant")
	sy = ndimage.sobel(tempdata, axis = 1, mode = "constant")
	e = np.hypot(sx, sy)
	print_sdata(sx, sy, e)
	temp = Map((e, tempheader))
	temp.e_img(K, SAVEPATH + "enhanced/AIA304", 250)
	RECORDER.info_text("Enhanced AIA304 image data saved")

	tempdata = K335[K][0] / K335[K][1]
	tempheader = K335[K][3]
	sx = ndimage.sobel(tempdata, axis = 0, mode = "constant")
	sy = ndimage.sobel(tempdata, axis = 1, mode = "constant")
	e = np.hypot(sx, sy)
	print_sdata(sx, sy, e)
	temp = Map((e, tempheader))
	temp.e_img(K, SAVEPATH + "enhanced/AIA335", 250)
	RECORDER.info_text("Enhanced AIA335 image data saved")

for K in tqdm(range(N), desc = "Generating binary images"):
	temp_im = Image.open("%senhanced/AIA94/enhanced_%04d.png" % (SAVEPATH, K))
	gr = gen_bin_img(temp_im)
	plt.imsave("%sbinary/AIA94/binary_%04d.png" % (SAVEPATH, K), gr, cmap = "gray")

	temp_im = Image.open("%senhanced/AIA131/enhanced_%04d.png" % (SAVEPATH, K))
	gr = gen_bin_img(temp_im)
	plt.imsave("%sbinary/AIA131/binary_%04d.png" % (SAVEPATH, K), gr, cmap = "gray")

	temp_im = Image.open("%senhanced/AIA171/enhanced_%04d.png" % (SAVEPATH, K))
	gr = gen_bin_img(temp_im)
	plt.imsave("%sbinary/AIA171/binary_%04d.png" % (SAVEPATH, K), gr, cmap = "gray")

	temp_im = Image.open("%senhanced/AIA193/enhanced_%04d.png" % (SAVEPATH, K))
	gr = gen_bin_img(temp_im)
	plt.imsave("%sbinary/AIA193/binary_%04d.png" % (SAVEPATH, K), gr, cmap = "gray")

	temp_im = Image.open("%senhanced/AIA211/enhanced_%04d.png" % (SAVEPATH, K))
	gr = gen_bin_img(temp_im)
	plt.imsave("%sbinary/AIA211/binary_%04d.png" % (SAVEPATH, K), gr, cmap = "gray")

	temp_im = Image.open("%senhanced/AIA304/enhanced_%04d.png" % (SAVEPATH, K))
	gr = gen_bin_img(temp_im)
	plt.imsave("%sbinary/AIA304/binary_%04d.png" % (SAVEPATH, K), gr, cmap = "gray")

	temp_im = Image.open("%senhanced/AIA335/enhanced_%04d.png" % (SAVEPATH, K))
	gr = gen_bin_img(temp_im)
	plt.imsave("%sbinary/AIA335/binary_%04d.png" % (SAVEPATH, K), gr, cmap = "gray")

for K in tqdm(range(N), desc = "Generating traced images"):
	pass

FPS = 24

RECORDER.sys_text("================ Generating raw videos ================")
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sraw/AIA94/raw_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sraw/AIA94_raw.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sraw/AIA131/raw_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sraw/AIA131_raw.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sraw/AIA171/raw_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sraw/AIA171_raw.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sraw/AIA193/raw_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sraw/AIA193_raw.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sraw/AIA211/raw_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sraw/AIA211_raw.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sraw/AIA304/raw_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sraw/AIA304_raw.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sraw/AIA335/raw_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sraw/AIA335_raw.mp4" % (FPS, SAVEPATH, N, SAVEPATH))

os.system("ffmpeg -loglevel panic -y -i %sraw/AIA94_raw.mp4 -i %sraw/AIA131_raw.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sraw/temp1.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sraw/AIA171_raw.mp4 -i %sraw/AIA193_raw.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sraw/temp2.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sraw/AIA211_raw.mp4 -i %sraw/AIA304_raw.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sraw/temp3.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sraw/temp1.mp4 -i %sraw/temp2.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sraw/temp4.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sraw/temp3.mp4 -i %sraw/AIA335_raw.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sraw/temp5.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sraw/temp4.mp4 -i %sraw/temp5.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sraw/temp6.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sraw/temp6.mp4 -filter:v 'crop=8400:1200:0:0' %sraw/COMBINED_raw.mp4" % (SAVEPATH, SAVEPATH))
os.system("rm %sraw/temp1.mp4 %sraw/temp2.mp4 %sraw/temp3.mp4 %sraw/temp4.mp4 %sraw/temp5.mp4 %sraw/temp6.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH, SAVEPATH, SAVEPATH, SAVEPATH))

RECORDER.sys_text("================ Generating enhanced videos ================")
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %senhanced/AIA94/enhanced_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %senhanced/AIA94_enhanced.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %senhanced/AIA131/enhanced_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %senhanced/AIA131_enhanced.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %senhanced/AIA171/enhanced_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %senhanced/AIA171_enhanced.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %senhanced/AIA193/enhanced_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %senhanced/AIA193_enhanced.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %senhanced/AIA211/enhanced_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %senhanced/AIA211_enhanced.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %senhanced/AIA304/enhanced_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %senhanced/AIA304_enhanced.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %senhanced/AIA335/enhanced_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %senhanced/AIA335_enhanced.mp4" % (FPS, SAVEPATH, N, SAVEPATH))

os.system("ffmpeg -loglevel panic -y -i %senhanced/AIA94_enhanced.mp4 -i %senhanced/AIA131_enhanced.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %senhanced/temp1.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %senhanced/AIA171_enhanced.mp4 -i %senhanced/AIA193_enhanced.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %senhanced/temp2.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %senhanced/AIA211_enhanced.mp4 -i %senhanced/AIA304_enhanced.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %senhanced/temp3.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %senhanced/temp1.mp4 -i %senhanced/temp2.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %senhanced/temp4.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %senhanced/temp3.mp4 -i %senhanced/AIA335_enhanced.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %senhanced/temp5.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %senhanced/temp4.mp4 -i %senhanced/temp5.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %senhanced/temp6.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %senhanced/temp6.mp4 -filter:v 'crop=8400:1200:0:0' %senhanced/COMBINED_enhanced.mp4" % (SAVEPATH, SAVEPATH))
os.system("rm %senhanced/temp1.mp4 %senhanced/temp2.mp4 %senhanced/temp3.mp4 %senhanced/temp4.mp4 %senhanced/temp5.mp4 %senhanced/temp6.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH, SAVEPATH, SAVEPATH, SAVEPATH))

RECORDER.sys_text("================ Generating binary videos ================")
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sbinary/AIA94/binary_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sbinary/AIA94_binary.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sbinary/AIA131/binary_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sbinary/AIA131_binary.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sbinary/AIA171/binary_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sbinary/AIA171_binary.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sbinary/AIA193/binary_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sbinary/AIA193_binary.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sbinary/AIA211/binary_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sbinary/AIA211_binary.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sbinary/AIA304/binary_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sbinary/AIA304_binary.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sbinary/AIA335/binary_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sbinary/AIA335_binary.mp4" % (FPS, SAVEPATH, N, SAVEPATH))

os.system("ffmpeg -loglevel panic -y -i %sbinary/AIA94_binary.mp4 -i %sbinary/AIA131_binary.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sbinary/temp1.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sbinary/AIA171_binary.mp4 -i %sbinary/AIA193_binary.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sbinary/temp2.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sbinary/AIA211_binary.mp4 -i %sbinary/AIA304_binary.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sbinary/temp3.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sbinary/temp1.mp4 -i %sbinary/temp2.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sbinary/temp4.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sbinary/temp3.mp4 -i %sbinary/AIA335_binary.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sbinary/temp5.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sbinary/temp4.mp4 -i %sbinary/temp5.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sbinary/temp6.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sbinary/temp6.mp4 -filter:v 'crop=8400:1200:0:0' %sbinary/COMBINED_binary.mp4" % (SAVEPATH, SAVEPATH))
os.system("rm %sbinary/temp1.mp4 %sbinary/temp2.mp4 %sbinary/temp3.mp4 %sbinary/temp4.mp4 %sbinary/temp5.mp4 %sbinary/temp6.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH, SAVEPATH, SAVEPATH, SAVEPATH))

RECORDER.sys_text("================ Generating edge videos ================")
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sedge/AIA94/edge_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sedge/AIA94_edge.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sedge/AIA131/edge_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sedge/AIA131_edge.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sedge/AIA171/edge_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sedge/AIA171_edge.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sedge/AIA193/edge_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sedge/AIA193_edge.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sedge/AIA211/edge_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sedge/AIA211_edge.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sedge/AIA304/edge_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sedge/AIA304_edge.mp4" % (FPS, SAVEPATH, N, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -f image2 -start_number 0 -framerate %d -i %sedge/AIA335/edge_%%04d.png -vframes %d -q:v 2 -vcodec mpeg4 -b:v 800k %sedge/AIA335_edge.mp4" % (FPS, SAVEPATH, N, SAVEPATH))

os.system("ffmpeg -loglevel panic -y -i %sedge/AIA94_edge.mp4 -i %sedge/AIA131_edge.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sedge/temp1.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sedge/AIA171_edge.mp4 -i %sedge/AIA193_edge.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sedge/temp2.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sedge/AIA211_edge.mp4 -i %sedge/AIA304_edge.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sedge/temp3.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sedge/temp1.mp4 -i %sedge/temp2.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sedge/temp4.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sedge/temp3.mp4 -i %sedge/AIA335_edge.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sedge/temp5.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sedge/temp4.mp4 -i %sedge/temp5.mp4 -filter_complex '[0:v]pad=iw*2:ih[int];[int][1:v]overlay=W/2:0[vid]' -map [vid] -c:v libx264 -crf 23 -preset veryfast %sedge/temp6.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH))
os.system("ffmpeg -loglevel panic -y -i %sedge/temp6.mp4 -filter:v 'crop=8400:1200:0:0' %sedge/COMBINED_edge.mp4" % (SAVEPATH, SAVEPATH))
os.system("rm %sedge/temp1.mp4 %sedge/temp2.mp4 %sedge/temp3.mp4 %sedge/temp4.mp4 %sedge/temp5.mp4 %sedge/temp6.mp4" % (SAVEPATH, SAVEPATH, SAVEPATH, SAVEPATH, SAVEPATH, SAVEPATH))

RECORDER.display_end_time("structure")