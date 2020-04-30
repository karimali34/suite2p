import os
import numpy as np
import glob
import natsort
import tifffile
import fbpca
from scipy.io import savemat, loadmat
import scipy.ndimage.morphology as ndimage
import scipy.signal as signal
import caiman.source_extraction.cnmf.deconvolution as deconv
#import sima.spikes as deconv
#import constrained_foopsi as deconv
import multiprocessing
import time
import skimage
from abfLoad import abfLoad

def do_deconv(results_dir, frameinterval, nframes, expt_dirs, abf_dir=None, nplanes=1, transpose=False, force=False):
	nf_sum = np.cumsum(np.append([0], nframes))
	for i in range(len(nframes)):
		print('Running expt_dir {} ({} frames)'.format(expt_dirs[i], nframes[i]))
		res_dir = os.path.abspath(os.path.join(results_dir, '..', str(expt_dirs[i])))
		for p in range(nplanes):
			if nplanes > 1:
				res_dir2 = os.path.join(res_dir, 'suite2p/plane{}'.format(p))
			else:
				res_dir2 = res_dir
			if not os.path.isdir(res_dir2):
				os.makedirs(res_dir2)
			fnTimeCourses = os.path.join(res_dir2, 'timecourses.mat'.format(p))
			if os.path.isfile(fnTimeCourses) and not force:
				tmp = loadmat(fnTimeCourses)
				tcs = {}
				tcs['ratio'] = tmp['tcs']['ratio'][0][0]
			else:
				frame_start = nf_sum[i]
				frame_end = nf_sum[i+1]
				tcs = frExtractTimeCourses(results_dir, res_dir2, abf_dir, frameinterval, frame_start, frame_end, p, transpose=transpose)
			genDeconv(res_dir2, tcs['ratio'])

def genDeconv(out_dir, ratio):
	c = np.zeros((ratio.shape[0], ratio.shape[1]))
	sp = np.zeros((ratio.shape[0], ratio.shape[1]))
	#r2 = np.transpose(ratio).flatten()
	#t = time.time()
	#print('Generating deconvolution')
	#(c2, bl, c1, g, sn, sp2, lam) = deconv.constrained_foopsi(r2, p=2, verbosity=True, method_deconvolution='cvxpy')
	#print('Took {}'.format(time.time() - t))
	#c = np.reshape(c2, (ratio.shape[0], ratio.shape[1]))
	#sp = np.reshape(sp2, (ratio.shape[0], ratio.shape[1]))
	for i in range(ratio.shape[1]):
		print('Generating deconvolution for neuron {}'.format(i+1))
		t = time.time()
		(c[:, i], bl, c1, g, sn, sp[:, i], lam) = deconv.constrained_foopsi(ratio[:, i], p=2, verbosity=True, method_deconvolution='oasis')
		print('Took {}'.format(time.time() - t))
	#np.fft.restore_all()
	#for i in range(ratio.shape[1]):
	#	(sp, c, params) = deconv.spike_inference(ratio[:, i], mode='psd')

	savemat(os.path.join(out_dir, 'deconv.mat'), {'deconv': sp}, do_compression=True)
	savemat(os.path.join(out_dir, 'ratio_model.mat'), {'ratio_model': c}, do_compression=True)


def frExtractTimeCourses(reg_dir, results_dir, abf_dir, frameinterval, frame_start, frame_end, plane, overwrite=True, updateRaw=True, adaptBaseLine=False, ringSubtract=True, maskOp='manual', maskAlign='aligned', transpose=False):
	fnTimeCourses = os.path.join(results_dir, 'timecourses.mat')

	reg_file = os.path.join(reg_dir, 'suite2p/plane{}/data.bin'.format(plane))

	# use_bin = False
	l = []
	# if os.path.isfile(reg_file):
	# 	use_bin = True
	# else:
	# 	l = glob.glob(os.path.join(fn, '*.tif'))
	# 	l = natsort.natsorted(l)
	# 	nfiles = len(l)
	# 	group_size = 256
	# 	n_group = np.ceil(nfiles / group_size)
	# 	n_group = int(n_group)

	tcs = {}

	if updateRaw:
		ops = np.load(os.path.join(reg_dir, 'suite2p/plane{}/ops.npy'.format(plane)), allow_pickle=True).item()
		dims = (ops['Ly'], ops['Lx'])
		if transpose:
			dims = (ops['Lx'], ops['Ly'])
		print('Loading Masks')
		if maskOp in ['manual', 'auto', 'active', 'masks_neuronsZoom']:
			(maskNeurons, maskRings) = doLoadMasks(reg_dir, dims, plane)
		elif maskOp in ['aligned', 'activeAligned']:
			(tmpMask, maskRings) = doLoadMasks(reg_dir, dims, plane)
			maskNeurons = np.squeeze(tmpMask[:, :, 0])
		savemat(os.path.join(results_dir, 'masks.mat'), {'maskNeurons': maskNeurons, 'maskRings': maskRings})
		print('Done loading masks')
		# maskRings = doMaskRings(maskNeurons, 1, 8)
		tcs['nSamples'] = ops['nframes']
		tmp = maskNeurons.flatten()
		tcs['cellIDs'] = np.unique(tmp[np.where(tmp > 0)])
		tcs['nCells'] = tcs['cellIDs'].size
		#tcs['raw'] = np.ones((tcs['nSamples'], np.max(tcs['cellIDs'])), dtype=np.float32)
		#tcs['ring'] = np.ones((tcs['nSamples'], np.max(tcs['cellIDs'])), dtype=np.float32)
		# iX = 0
		# for i_group in range(n_group):
		# if i_group == n_group - 1:
		# 	filens = np.arange(i_group*group_size, nfiles)
		# else:
		# 	filens = np.arange(i_group*group_size, (i_group + 1)*group_size)
		# num_frames = sizetiff(l[filens[0]:(filens[-1]+1)])
		# stack = np.zeros((num_frames, ) + dims, dtype=np.uint16)

		print('Loading reg file from {}'.format(reg_file))
		reg_data = np.memmap(reg_file, dtype=np.int16, mode='r')
		#stack = np.reshape(reg_data, (-1, ops['Lx'], ops['Ly']))
		stack = np.reshape(reg_data, (-1,) + dims)
		stack_mean = np.mean(stack[frame_start:frame_end, :, :], axis=0)

		tifffile.imwrite(os.path.join(results_dir, 'avgstack.tif'), stack_mean.astype(np.int16))
		savemat(os.path.join(results_dir, 'avgstack.mat'), {'avg_stack': stack_mean.astype(np.float32)})

		stack_max = np.max(stack[frame_start:frame_end, :,  :], axis=0)

		tifffile.imwrite(os.path.join(results_dir, 'maxstack.tif'), stack_max.astype(np.int16))
		savemat(os.path.join(results_dir, 'maxstack.mat'), {'max_stack': stack_max.astype(np.float32)})
		# for i in filens:
		# 	tmp_numframes = sizetiff([l[i]])
		# 	stack[(i*tmp_numframes):((i+1)*tmp_numframes), :, :] = tiffile.imread(l[i])
		# 	print('Loaded {}/{} tiffs'.format(i+1, len(filens)))
		print('Getting timecourses')
		# tcs['raw'][iX:(iX+stack.shape[0]), :] = stackGetTimeCourses(stack, maskNeurons, 'mean')
		# tcs['ring'][iX:(iX+stack.shape[0]), :] = stackGetTimeCourses(stack, maskRings, 'mean')
		tcs['raw'] = stackGetTimeCourses(stack[frame_start:frame_end,  :, :], maskNeurons, 'mean')
		tcs['ring'] = stackGetTimeCourses(stack[frame_start:frame_end, :, :], maskRings, 'mean')

		# iX += stack.shape[0]
	else:
		if os.path.isfile(fnTimeCourses):
			tcs = loadmat(fnTimeCourses)
			tcs = tcs['tcs']
		else:
			print('File not found: {}'.format(fnTimeCourses))

	#if adaptBaseLine:
	#	tcs['baseline'] = tcGetBaselineAdapt(tcs['raw'])
	#else:
	tcs['baseline'] = tcGetBaseline(tcs['raw'])

	if ringSubtract:
		print('Performing ring subtract')
		(u, s, v) = fbpca.pca(tcs['ring'], 1, raw=True)
		tcs['neuropil'] = np.matmul(np.matmul(u, np.reshape(s, (1, 1))), v)

	print('Calculating ratio')
	if ringSubtract:
		neuropil_zero = tcs['neuropil'] - np.nanmean(tcs['neuropil'], axis=0)
		tcs['ratio'] = 100 * (tcs['raw'] - neuropil_zero - tcs['baseline']) / tcs['baseline']
	else:
		tcs['ratio'] = 100 * (tcs['raw'] - tcs['baseline']) / tcs['baseline']

	if abf_dir is None:
		tcs['tt'] = np.arange(tcs['raw'].shape[0]) * frameinterval
	else:
		tt = []
		rax = 0.0
		for x in abf_dir:
			abf_o = abfLoad(x)
			frame_ts = abf_o.frame_ts()
			tt.append( np.add( frame_ts, rax + 1 / abf_o.Fs() ) )
			rax += frame_ts[-1]
		tt = np.concatenate(tt)
		tcs['tt'] = tt
	savemat(fnTimeCourses, {'tcs': tcs}, do_compression=True)
	return tcs

def tcGetBaseline(x, ds=16):
	ncells = x.shape[1]
	m = np.mean(x, axis=0)
	xm = x - m
	xint = np.cumsum(xm, axis=0)
	xint2 = signal.decimate(xint, ds, axis=0)
	N = 4
	F = 21
	x0 = signal.savgol_filter(xint2, F, N, deriv=0, axis=0)
	x1 = signal.savgol_filter(xint2, F, N, deriv=1, axis=0)
	x2 = 2*signal.savgol_filter(xint2, F, N, deriv=2, axis=0)
	x0 = np.roll(x0, -int(np.floor(F/2)), axis=0)
	x1 = np.roll(x1, -int(np.floor(F/2)), axis=0)
	x2 = np.roll(x2, -int(np.floor(F/2)), axis=0)

	b = np.zeros(ncells)
	for i in range(ncells):
		print('Getting baseline for {}'.format(i+1))
		ind1 = np.where(x1[:, i] == 0)[0]
		ind2 = np.where((x1[:-1:2, i] * x1[1::2, i]) < 0)[0]
		bp = np.sort(np.concatenate((ind1, ind2)))
		xlin = x0[:, i] - signal.detrend(x0[:, i], type='linear', bp=bp)
		xlinp = np.diff(xlin)/ds
		xlinp_neg = xlinp[np.where(xlinp < 0)]

		if xlinp_neg.shape[0] > 0:
			b[i] = np.percentile(xlinp_neg, 10)
		else:
			b[i] = 0;
	b = b + m
	return b

def genRing(maskNeurons, inner_struct, outer_struct, i):
	print('Getting ring mask for neuron {}'.format(i))
	curr_mask = (maskNeurons == i)
	innerMask = ndimage.binary_dilation(curr_mask, inner_struct)
	outerMask = ndimage.binary_dilation(curr_mask, outer_struct)
	sel = (outerMask & ~innerMask) == 1
	return sel

def doLoadMasks(results_dir, dims, plane=0):
	maskNeurons = np.zeros(dims, dtype=np.uint32)
	maskNeurons = maskNeurons.flatten()
	maskRings = np.zeros(dims, dtype=np.uint32)

	iscell = np.load(os.path.join(results_dir, 'suite2p/plane{}/iscell.npy'.format(plane)), allow_pickle=True)
	stat = np.load(os.path.join(results_dir, 'suite2p/plane{}/stat.npy'.format(plane)), allow_pickle=True)

	cell_num = 1
	for i in range(stat.shape[0]):
		if iscell[i, 0]:
			print('Getting mask for neuron {}'.format(i))
			cell = stat[i]
			maskNeurons[cell['ipix']] = cell_num
			cell_num += 1

	maskNeurons = maskNeurons.reshape(dims)

	props = skimage.measure.regionprops(maskNeurons)
	cent = [x.centroid[1] for x in props]
	idx = np.argsort(cent)
	mask2 = np.zeros(maskNeurons.shape, dtype=np.uint32)
	for i in range(len(cent)):
		mask2[np.where(maskNeurons == (idx[i]+1))] = i+1

	maskNeurons = mask2

	(x, y) = np.meshgrid(np.arange(-1, 2), np.arange(-1, 2))
	rad = np.sqrt(x**2 + y**2)
	inner_struct = rad <= 1
	(x, y) = np.meshgrid(np.arange(-8, 9), np.arange(-8, 9))
	rad = np.sqrt(x**2 + y**2)
	outer_struct = rad <= 8

	curr_map = [(maskNeurons, inner_struct, outer_struct)] * (cell_num - 1)
	curr_map = [curr_map[i-1] + (i, ) for i in range(1, cell_num)]
	with multiprocessing.Pool(None) as p:
		all_sel = p.starmap(genRing, curr_map)
		for i in range(len(all_sel)):
			maskRings[all_sel[i]] = i+1
	# for i in range(1,cell_num):
	# 	print('Getting ring mask for neuron {}'.format(i))
	# 	curr_mask = (maskNeurons == i)
	# 	innerMask = ndimage.binary_dilation(curr_mask, inner_struct)
	# 	outerMask = ndimage.binary_dilation(curr_mask, outer_struct)
	# 	sel = (outerMask & ~innerMask) == 1
	# 	maskRings[sel] = i

	return (maskNeurons, maskRings)

def sizetiff(tiffs):
	nframes = 0
	for t in tiffs:
		with tifffile.TiffFile(t) as tmp:
			nframes += len(tmp.pages)
	return nframes

def stackGetTimeCourses(stack, mask, type='mean'):
	(nFrames, nRows, nCols) = stack.shape

	if nRows != mask.shape[0] or nCols != mask.shape[1]:
		print('Size mismatch between stack and mask')

	stackCols = np.reshape(stack, (nFrames, nRows*nCols))
	labelCols = np.reshape(mask, (nRows*nCols))

	unqLabels = np.setdiff1d(np.unique(labelCols), [0])
	unqLabels = unqLabels[np.where(~np.isnan(unqLabels))]

	nCells = unqLabels.shape[0]

	if type == 'mean':
		tc = np.random.randint(10, size=(nFrames, np.max(unqLabels))).astype(np.float64)
		for ic in range(nCells):
			print('Getting timecourse for {}/{}'.format(unqLabels[ic], nCells))
			tc[:, ic] = np.squeeze(np.nanmean(stackCols[:, np.where(labelCols == unqLabels[ic])], axis=2))
	elif type == 'min':
		tc = np.random.randint(10, size=(nFrames, np.max(unqLabels))).astype(np.float64)
		for ic in range(nCells):
			tc[:, ic] = np.squeeze(np.nanmin(stackCols[:, np.where(labelCols == unqLabels[ic])], axis=2))
	elif type == 'none':
		if nCells != 1:
			raise ValueError('Only one cell allowed when using none method')

		#nPix = np.nansum(labelCols == 1)
		tc = np.transpose(stackCols[:, labelCols == 1])
	else:
		raise ValueError('Invalid reduce method')

	return tc

if __name__ == '__main__':
	do_deconv('/media/storage/data/Bailey/results/Bailey/2020_02_24/1', 0.5/19.066, [500], [1], nplanes=64, force=True)
