import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import math
import shutil
import os
import csv
import getpass

RUNTIME_COL_NUM = 3
PG_WALK_LATENCY_COL_NUM = 2

system_labels = [
	'Vanilla Linux', 
	'EMT-Linux', 
]

# TODO: change this because we don't have geo_mean in the csv
def perf_from_csv(path):
    df = pd.read_csv(path, index_col=0)
    # return np.array(df['avg_run_time'])
    selected_benchs = ~df.index.isin(["graphbig_bc", "mummer"]) 
    return np.array(df[selected_benchs]['avg_run_time'])
    # return np.array(df['geo_mean'])

import os
import sys
from subprocess import Popen

def svg2pdf(src):
    dst = src.replace('.svg', '.pdf')
    print('Rendering: ', src, ' -> ', dst)
    x = Popen(['inkscape', src, \
        '--export-pdf=%s' % dst])
    try:
        waitForResponse(x)
    except:
        return False

def waitForResponse(x): 
    out, err = x.communicate() 
    if x.returncode < 0: 
        r = "Popen returncode: " + str(x.returncode) 
        raise OSError(r)

# RAW_DATA_DIR = '../raw_data/xeon/'
# app_tag = '_7avg_'

# vanilla_path = os.path.join(RAW_DATA_DIR, '5.15.0-vanilla_THP_never_app' + app_tag + '.csv')
# gen_x86_path = os.path.join(RAW_DATA_DIR, '5.15.0-gen-x86_THP_never_app' + app_tag + '.csv')

# get_yerrors(vanilla_path, gen_x86_path)

def get_kernel_version():
    try:
        output = subprocess.check_output(["uname", "-r"], universal_newlines=True)
        return output.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        return None
    
RAW_DATA_DIR = f'./ae_result/{getpass.getuser()}'
OUTPUT_DIR = f'./ae_result/{getpass.getuser()}/graphs'
KERNEL = get_kernel_version()

app_bench_list = [
        # 'BC',
        'BFS',
        'DFS',
        'DC',
        'SSSP',
        'CC',
        'TC',
        'PR',
        'Sysbench',
        'GUPS',
        # 'MUMmer', # do not reorder the last three - they will overlap other labels
        # 'csynb'
]

# data input
import argparse
parser = argparse.ArgumentParser(description='Plotting script')
parser.add_argument('--input')
parser.add_argument('--kernel')
parser.add_argument('--output')
args = parser.parse_args()
if args.input:
    RAW_DATA_DIR = args.input
if args.kernel:
    KERNEL = args.kernel
if args.output:
    OUTPUT_DIR = args.output

if (KERNEL == 'vanilla'):
    KERNEL = '5.15.0-vanilla'
elif (KERNEL == 'gen-x86'):
    KERNEL = '5.15.0-gen-x86'

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# label of the y-axis
ylabel1 = "Norm. Runtime"

sheetX1 = system_labels.copy()

sheetY1 = app_bench_list.copy()

vanilla_no_THP = perf_from_csv(path= os.path.join(RAW_DATA_DIR, '5.15.0-vanilla_THP_never_app.csv'))
gen_x86_no_THP = perf_from_csv(path= os.path.join(RAW_DATA_DIR, '5.15.0-gen-x86_THP_never_app.csv'))

# print(vanilla_no_THP)
# print(gen_x86_no_THP)

datasheet1 = np.column_stack((vanilla_no_THP, gen_x86_no_THP))
datadiv1 = vanilla_no_THP
# y_errors3 = get_yerrors(vanilla_path, gen_x86_path)
# # print(datasheet1)
# # print(y_errors3)
# y_errors3[0] = None
# print(y_errors3)
# transpose the datasheet
transpose1 = False

name1 = 'Application speedup'

yformat1 = '%.1f'

# print(datasheet1 / datadiv1[:,None])
# build dataframe
# df_perf = pd.DataFrame(datasheet1 / datadiv1[:,None], columns = sheetX1, index = sheetY1)
# print(df_perf)

# ylabel2 = "Page Walk Speedup"

# sheetX2 = system_labels.copy()

# sheetY2 = app_bench_list.copy()

# walk_vanilla_no_THP = pgwalk_speedup_from_csv(path= os.path.join(RAW_DATA_DIR, '5.15.0-vanilla_THP_never_latency.csv'))
# walk_gen_x86_no_THP = pgwalk_speedup_from_csv(path= os.path.join(RAW_DATA_DIR, '5.15.0-gen-x86_THP_never_latency.csv'))

# datasheet2 = np.column_stack((walk_vanilla_no_THP, walk_gen_x86_no_THP))
# datadiv2 = walk_vanilla_no_THP

# # transpose the datasheet
# transpose2 = False

# name2 = 'Page walk speedup'

# yformat2 = '%.1f'

# for i in range(0, len(sheetX1)):
#     appTbl = datasheet1
#     pwTbl = datasheet2

#     print(sheetX1[i])

#     vanillaApp = appTbl[:, 0]
#     dmtApp = appTbl[:, -1]
#     systemApp = appTbl[:, i]
#     print("App DMT BP: ", (dmtApp / systemApp).mean())

#     vanillaPW = pwTbl[:, 0]
#     dmtPW = pwTbl[:, -1]
#     systemPW = pwTbl[:, i]
#     print("PW DMT BP: ", (dmtPW / systemPW).mean())

#     print()

# for i in range(0, len(sheetX3)):
#     appTbl = datasheet3
#     pwTbl = datasheet4

#     print(sheetX3[i])

#     vanillaApp = appTbl[:, 0]
#     dmtApp = appTbl[:, -1]
#     systemApp = appTbl[:, i]
#     print("App DMT HP: ", (dmtApp / systemApp).mean())
        
#     vanillaPW = pwTbl[:, 0]
#     dmtPW = pwTbl[:, -1]
#     systemPW = pwTbl[:, i]
#     print("PW DMT HP: ", (dmtPW / systemPW).mean())

#     print()

# global config

# name of the exported file
filename = 'radix.svg'

# release mode (generate pdf and copy mkplot)
releasePdf = True
releaseSrc = False

# color of each bar (bar clrs, texture clrs, texture)
# count >= len(sheetX), redundant colors will be ignored
# available texture: ['/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']
# color = [
# 	['#808080', '#000000', None], # Vanilla
# 	['#FE5E41', '#000000', '\\'], # Hyperlane
# ]

color = [
	['#808080', '#000000', None], # Vanilla
	['#96ceb4', '#000000', None], # Hyperlane
]

# % width of the bar group
barWidth = 0.8

# folder of the exported file
folder = '.'

# rows of legends
legendRows = 1

# plot size
plotSize = (8, 4.3)

# font size
fontSize = 30
fontName = 'Times New Roman'

# pad image height by this value, used to save space for the legend
heightMargin = 1.1

# legend offset, used to adjust legend's place on plot
legendOffset = 0.95

# legend width, relative to figure width
legendWidth = 0.9

legendSpacing = 10

# plotting framework

plt.rcParams.update({ 'font.size': fontSize, 'font.family': fontName })

def post_process(ax, ylabel, sheetX, sheetY, datasheet, datadiv, errors, transpose, name, yformat):
	shape = datasheet.shape
	datasheet = datasheet / datadiv[:,None]
	datasheet = datasheet.reshape(shape)

	# append average at the end
	avg = np.mean(datasheet, axis=0)
	# print(np.max(datasheet, axis=0) -1, 1-np.min(datasheet, axis=0))
	# print(avg)
	# print(np.std(datasheet, axis=0))
	# datasheet = np.vstack((datasheet, avg))
	sheetY_ = sheetY.copy()
	# sheetY_.append('Mean')

	# print(datasheet)
	# print(sheet/Y_)
	maxY = np.amax(datasheet) * heightMargin

	if transpose:
		datasheet = datasheet.T
		(sheetY_, sheetX) = (sheetX, sheetY_)

	df = pd.DataFrame(datasheet, columns = sheetX, index = sheetY_)
	if (len(errors) > 0):
		df.plot(ax = ax, kind = 'bar', legend = False, width = barWidth, yerr=errors, capsize=4)
	else:
		df.plot(ax = ax, kind = 'bar', legend = False, width = barWidth)
	# plt.errorbar(df.index, df['Vanilla Linux'], yerr=y_err, fmt='o', ecolor='green', elinewidth=2, capsize=5, capthick=2, alpha=0.7)

	
	# plt.errorbar(ax = ax, yerr=y_err, fmt='-', ecolor='blue', capsize=5, linestyle='')

	colors = color[0 : len(sheetX)]

	bars = ax.patches
	colors = [item for item in colors for i in range(len(df))]

	for bar, clr in zip(bars, colors): # set bar style
		bar.set_facecolor(clr[0])
		bar.set_edgecolor(clr[1])
		bar.set_hatch(clr[2])

	# ax.set_xlabel(name) # clear x label
	ax.set_ylabel(ylabel)
	ax.set_ylim([0, maxY])
	#ax.grid(axis = 'y', linestyle = 'dotted') # add horizental grid lines
	ax.locator_params(nbins=8, axis='y') # plot more y ticks
	ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter(yformat))

	ax.tick_params(axis="x", labelsize=fontSize - 6) # prevent x labels from displayed vertically
	plt.setp(ax.xaxis.get_majorticklabels(), rotation=40, ha="right", rotation_mode="anchor") 
 
 # image layout

fig, ax = plt.subplots(1, 1, figsize = plotSize)

fig.tight_layout(h_pad=3)

# application no THP
post_process(ax, ylabel1, sheetX1, sheetY1, datasheet1, datadiv1, [], transpose1, name1, yformat1)
# page walk no THP
# post_process(ax[1], ylabel2, sheetX2, sheetY2, datasheet2, datadiv2, [], transpose2, name2, yformat2)

# application THP
# post_process(ax[1], ylabel3, sheetX3, sheetY3, datasheet3, datadiv3, [], transpose3, name3, yformat3)
# # page walk THP
# post_process(ax[0][1], ylabel4, sheetX4, sheetY4, datasheet4, datadiv4, [], transpose4, name4, yformat4)

# fig.text(0.215, -0.135, "(a) 4KB", fontsize=fontSize + 2, weight='bold', fontfamily='Times New Roman')
# fig.text(0.700, -0.135, "(b) THP", fontsize=fontSize + 2, weight='bold', fontfamily='Times New Roman')

if releasePdf:
	path = OUTPUT_DIR + '/' + filename
	fig.savefig(path, bbox_inches="tight")
	svg2pdf(path)