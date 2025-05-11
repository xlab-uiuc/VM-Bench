import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import math
import shutil
import os
import csv
from subprocess import Popen
import argparse
import getpass

system_labels = [
	'Vanilla Linux', 
	'EMT-Linux', 
]

RUNTIME_COL_NUM = 3
PG_WALK_LATENCY_COL_NUM = 2

INPUT_DIR = f'./ae_result/{getpass.getuser()}'
OUTPUT_DIR = './graphs'

def perf_from_csv(path):
    df = pd.read_csv(path, index_col=0)
    # return np.array(df['avg_run_time'])
    selected_benchs = ~df.index.isin(["graphbig_bc", "mummer"]) 
    return np.array(df[selected_benchs]['geo_mean'])
    # return np.array(df['geo_mean'])

def app_speedup_from_csv(path):
    return 1 / perf_from_csv(path)

def pgwalk_latency_from_csv(path):
    df = pd.read_csv(path, index_col=0)
    # return np.array(df['avg_run_time'])
    selected_benchs = ~df.index.isin(["APP graphbig_bc", "APP mummer"]) 
    return np.array(df[selected_benchs]['avg_latency'])

def pgwalk_speedup_from_csv(path):
    return 1 / pgwalk_latency_from_csv(path)

def get_overall_throughput(workload, kernel, thp, key):
    filename = f'{INPUT_DIR}/{workload}_{kernel}_THP_{thp}/summary.csv'
    # print(filename)
    df = pd.read_csv(filename, index_col=0)

    return df[key]['mean']

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
    
    
parser = argparse.ArgumentParser()
parser.add_argument("--input")
parser.add_argument("--output")
args = parser.parse_args()
if args.input:
    INPUT_DIR = args.input
    
if args.output:
    OUTPUT_DIR = args.output

# data input

# label of the y-axis
ylabel1 = "Norm. Throughput"

sheetX1 = system_labels.copy()

sheetY1 = []

sheetY1.append('Redis')
sheetY1.append('Memcached')
sheetY1.append('PostgreSQL')

vanilla_no_THP = []
gen_x86_no_THP = []

kernel_choice = '5.15.0-vanilla'
real_app_vanilla_no_THP = np.array([
    get_overall_throughput('redis', kernel_choice, 'never', 'running_phase_precise_throughput'),
    get_overall_throughput('memcached', kernel_choice, 'never', 'running_phase_precise_throughput'),
    get_overall_throughput('postgres', kernel_choice, 'never', 'read_precise_throughput'),
])

# print(real_app_vanilla_no_THP)
kernel_choice = '5.15.0-gen-x86'
real_app_gen_x86_no_THP = np.array([
    # 651223.379,
    get_overall_throughput('redis', kernel_choice, 'never', 'running_phase_precise_throughput'),
    get_overall_throughput('memcached', kernel_choice, 'never', 'running_phase_precise_throughput'),
    get_overall_throughput('postgres', kernel_choice, 'never', 'read_precise_throughput'),
])
# print(real_app_gen_x86_no_THP)

vanilla_no_THP = np.append(vanilla_no_THP, real_app_vanilla_no_THP)
gen_x86_no_THP = np.append(gen_x86_no_THP, real_app_gen_x86_no_THP)
datasheet1 = np.column_stack((vanilla_no_THP, gen_x86_no_THP))
datadiv1 = vanilla_no_THP
# y_errors3 = get_yerrors(vanilla_path, gen_x86_path)
# print(datasheet1)
transpose1 = False
name1 = 'Application speedup'
yformat1 = '%.1f'

# print(np.mean(datasheet1 / datadiv1[:,None]))

# data input

# label of the y-axis
ylabel2 = "Norm. Avg. Latency"

sheetX2 = system_labels.copy()

sheetY2 = sheetY1.copy()


vanilla_no_THP = []
gen_x86_no_THP = []

kernel_choice = '5.15.0-vanilla'
real_app_vanilla_no_THP = np.array([
    get_overall_throughput('redis', kernel_choice, 'never', 'running_phase_precise_avg_latency'),
    get_overall_throughput('memcached', kernel_choice, 'never', 'running_phase_precise_avg_latency'),
    get_overall_throughput('postgres', kernel_choice, 'never', 'read_precise_avg_latency'),
])



# print(real_app_vanilla_no_THP)
kernel_choice = '5.15.0-gen-x86'
real_app_gen_x86_no_THP = np.array([
    # 651223.379,
    get_overall_throughput('redis', kernel_choice, 'never', 'running_phase_precise_avg_latency'),
    get_overall_throughput('memcached', kernel_choice, 'never', 'running_phase_precise_avg_latency'),
    get_overall_throughput('postgres', kernel_choice, 'never', 'read_precise_avg_latency'),
])

# print(real_app_gen_x86_no_THP)

vanilla_no_THP = np.append(vanilla_no_THP, real_app_vanilla_no_THP)
gen_x86_no_THP = np.append(gen_x86_no_THP, real_app_gen_x86_no_THP)

# vanilla_no_THP = app_speedup_from_csv(path= os.path.join(RAW_DATA_DIR, '5.15.0-vanilla_THP_never_app' + app_tag + '.csv'))
# gen_x86_no_THP = app_speedup_from_csv(path= os.path.join(RAW_DATA_DIR, '5.15.0-gen-x86_THP_never_app' + app_tag + '.csv'))

datasheet2 = np.column_stack((vanilla_no_THP, gen_x86_no_THP))
datadiv2 = vanilla_no_THP
# y_errors3 = get_yerrors(vanilla_path, gen_x86_path)
# print(datasheet1)
# print(y_errors3)
# y_errors3[0] = None
# print(y_errors3)
# transpose the datasheet
transpose2 = False

name2 = 'Application speedup'

yformat2 = '%.1f'

# print(np.mean(datasheet2 / datadiv2[:,None]))

# data input

# label of the y-axis
ylabel3 = "Norm. P99 Latency"

sheetX3 = system_labels.copy()

sheetY3 = sheetY1.copy()


vanilla_no_THP = []
gen_x86_no_THP = []

kernel_choice = '5.15.0-vanilla'
real_app_vanilla_no_THP = np.array([
    get_overall_throughput('redis', kernel_choice, 'never', 'running_phase_precise_p99'),
    get_overall_throughput('memcached', kernel_choice, 'never', 'running_phase_precise_p99'),
    get_overall_throughput('postgres', kernel_choice, 'never', 'read_precise_p99'),
])



# print(real_app_vanilla_no_THP)
kernel_choice = '5.15.0-gen-x86'
real_app_gen_x86_no_THP = np.array([
    # 651223.379,
    get_overall_throughput('redis', kernel_choice, 'never', 'running_phase_precise_p99'),
    get_overall_throughput('memcached', kernel_choice, 'never', 'running_phase_precise_p99'),
    get_overall_throughput('postgres', kernel_choice, 'never', 'read_precise_p99'),
])

# print(real_app_gen_x86_no_THP)

vanilla_no_THP = np.append(vanilla_no_THP, real_app_vanilla_no_THP)
gen_x86_no_THP = np.append(gen_x86_no_THP, real_app_gen_x86_no_THP)

# vanilla_no_THP = app_speedup_from_csv(path= os.path.join(RAW_DATA_DIR, '5.15.0-vanilla_THP_never_app' + app_tag + '.csv'))
# gen_x86_no_THP = app_speedup_from_csv(path= os.path.join(RAW_DATA_DIR, '5.15.0-gen-x86_THP_never_app' + app_tag + '.csv'))

datasheet3 = np.column_stack((vanilla_no_THP, gen_x86_no_THP))
datadiv3 = vanilla_no_THP
# y_errors3 = get_yerrors(vanilla_path, gen_x86_path)
# print(datasheet3)
# print(y_errors3)
# y_errors3[0] = None
# print(y_errors3)
# transpose the datasheet
transpose3 = False

name3 = 'Application speedup'

yformat3 = '%.1f'

# print(np.mean(datasheet3 / datadiv3[:,None]))

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
plotSize = (4.5, 3.5)

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
	ax.set_ylabel(ylabel, fontsize = fontSize - 3)
	ax.set_ylim([0, maxY])
	ax.yaxis.set_label_coords(-0.23, 0.28)
	#ax.grid(axis = 'y', linestyle = 'dotted') # add horizental grid lines
	ax.locator_params(nbins=8, axis='y') # plot more y ticks
	ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter(yformat))

	ax.tick_params(axis="x", labelsize=fontSize - 6) # prevent x labels from displayed vertically
	plt.setp(ax.xaxis.get_majorticklabels(), rotation=40, ha="right", rotation_mode="anchor") 
 
 
fig, ax = plt.subplots(1, 1, figsize = plotSize)

fig.tight_layout(h_pad=5)

# application no THP
post_process(ax, ylabel1, sheetX1, sheetY1, datasheet1, datadiv1, [], transpose1, name1, yformat1)

# legend and output

handles, labels = ax.get_legend_handles_labels()
colCount = math.ceil(len(sheetX1) / legendRows)

filename = 'radix_real_app_throughput.svg'
if releasePdf:
	path = OUTPUT_DIR + '/' + filename
	fig.savefig(path, bbox_inches="tight")
	svg2pdf(path)

fig2, ax2 = plt.subplots(1, 1, figsize = plotSize)

fig2.tight_layout(h_pad=3)

# application no THP
post_process(ax2, ylabel2, sheetX2, sheetY2, datasheet2, datadiv2, [], transpose2, name2, yformat2)

handles, labels = ax2.get_legend_handles_labels()
colCount = math.ceil(len(sheetX1) / legendRows)

filename = 'radix_real_app_avg_latency.svg'
if releasePdf:
	path = OUTPUT_DIR + '/' + filename
	fig2.savefig(path, bbox_inches="tight")
	svg2pdf(path)

fig3, ax3 = plt.subplots(1, 1, figsize = plotSize)

fig3.tight_layout(h_pad=3)

# application no THP
post_process(ax3, ylabel3, sheetX3, sheetY3, datasheet3, datadiv3, [], transpose3, name3, yformat3)

handles, labels = ax3.get_legend_handles_labels()
colCount = math.ceil(len(sheetX1) / legendRows)

filename = 'radix_real_app_p99_latency.svg'
if releasePdf:
	path = OUTPUT_DIR + '/' + filename
	fig3.savefig(path, bbox_inches="tight")
	svg2pdf(path)