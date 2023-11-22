#!/usr/bin/env python
# coding: utf-8

# Tobias Rose 2023

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage.filters import uniform_filter
from scipy.signal import convolve
import cv2
import ipywidgets as widgets
from IPython.display import display
from natsort import natsorted, ns
import concurrent.futures
from multiprocessing import Pool, cpu_count
import imageio
import imageio.plugins.ffmpeg as ffmpeg
import os


# Define a function to display the volume with a slider
def display_volume_z(volume, scale, scalemin = 1, scalemax = 99.99):
    z_max = volume.shape[0] - 1
    if scale:
        vmin = np.percentile(volume[:500,:,:],scalemin)  
        vmax = np.percentile(volume[:500,:,:],scalemax)
    else:
        vmin = 0
        vmax = np.max(volume)
    def display_volume_z(z=0):
        plt.imshow(volume[z], cmap='gray', vmin=vmin, vmax=vmax)
        plt.axis('off')
        plt.show()
    widgets.interact(display_volume_z, z=widgets.IntSlider(min=0, max=z_max, step=1, value=0))


def rolling_average_filter(image_stack, kernel_size):
    image_stack = image_stack.astype('float32')
    
    # Define the kernel for the rolling average filter
    kernel = np.ones((kernel_size, 1, 1)) / kernel_size
    
    # Apply the rolling average filter along the z-axis
    filtered_image_stack = np.apply_along_axis(lambda m: np.convolve(m, kernel.flatten(), mode='same'), axis=0, arr=image_stack)
    
    return filtered_image_stack

def convolve_chunk(chunk_kernel_tuple):
    chunk, kernel = chunk_kernel_tuple
    return convolve(chunk, kernel, mode='same')

def rolling_average_filter_mt(image_stack, kernel_size):
    # Define the kernel for the rolling average filter
    kernel = np.ones((kernel_size, 1, 1)) / kernel_size

    # Define the overlap size
    overlap = kernel_size

    # Split the image stack into overlapping chunks
    chunks = []
    for i in range(0, image_stack.shape[0] - overlap, image_stack.shape[0] // cpu_count()):
        chunk_start = max(0, i - overlap)
        chunk_end = min(image_stack.shape[0], i + image_stack.shape[0] // cpu_count() + overlap)
        chunk = image_stack[chunk_start:chunk_end, :, :]
        chunks.append(chunk)

    # Process each chunk in parallel
    with Pool(processes=cpu_count()) as pool:
        filtered_chunks = pool.map(convolve_chunk, [(chunk, kernel) for chunk in chunks])

    # Trim the overlapping regions from the filtered chunks
    trimmed_chunks = []
    for i in range(len(filtered_chunks)):
        if i == 0:
            trimmed_chunk = filtered_chunks[i][overlap:, :, :]
        elif i == len(filtered_chunks) - 1:
            trimmed_chunk = filtered_chunks[i][:-overlap, :, :]
        else:
            trimmed_chunk = filtered_chunks[i][overlap:-overlap, :, :]
        trimmed_chunks.append(trimmed_chunk)

    # Concatenate the trimmed chunks in the original order
    filtered_image_stack = np.concatenate(trimmed_chunks, axis=0)

    return filtered_image_stack

# Rescale the image using multithreading
def rescale_image(running_z_projection, p1, p99):
    rescaled_image = (running_z_projection - p1) / (p99 - p1)
    rescaled_image[rescaled_image < 0] = 0
    rescaled_image[rescaled_image > 1] = 1

    # rescaled_image_8bit = cv2.convertScaleAbs(rescaled_image * 255 / np.max(rescaled_image))
    rescaled_image_8bit = cv2.convertScaleAbs(rescaled_image * 255 / 1)

    return rescaled_image_8bit

def process_image_part(running_z_projection, p1, p99, start, end):
    # Process a part of the image
    rescaled_image_part = rescale_image(running_z_projection[start:end], p1, p99)

    return rescaled_image_part

def rescale_image_multithreaded(running_z_projection, p1, p99):
    # Split the image into smaller parts
    num_pixels = len(running_z_projection)
    chunk_size = num_pixels // cpu_count()
    chunks = [(i * chunk_size, (i + 1) * chunk_size) for i in range(cpu_count())]
    chunks[-1] = (chunks[-1][0], num_pixels)

    # Process each part of the image using a separate thread
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_chunk = {executor.submit(process_image_part, running_z_projection, p1, p99, start, end): i for i, (start, end) in enumerate(chunks)}
        results = [None] * cpu_count()
        for future in concurrent.futures.as_completed(future_to_chunk):
            index = future_to_chunk[future]
            results[index] = future.result()

    # Combine the results
    rescaled_image = np.concatenate(results)

    return rescaled_image


def make_stack_movie(running_z_projection, filename, fpsset=120, p1set=1, p2set=99.995):
    print(filename)
    codecset = 'libx264'

    # Create an imageio VideoWriter object to write the video
    writer = imageio.get_writer(filename, fps=fpsset, codec=codecset, output_params=['-crf', '19'])

    # Calculate the 1st and 99th percentile
    p1, p99 = np.percentile(running_z_projection[:500,:,:], (p1set, p2set))

    # rescale to 8 bit
    rescaled_image_8bit = rescale_image_multithreaded(running_z_projection, p1, p99)

    for page in rescaled_image_8bit:
        writer.append_data(page)

    # Close the video writer
    writer.close()

    print(filename)

    return rescaled_image_8bit


def make_runninaverage_movie(path):
    # params_key = (imaging.ProcessingParamSet & 'paramset_idx = "4"').fetch('KEY')
    # reg_tiffs_available = (imaging.ProcessingParamSet & params_key).fetch("params")[0]['reg_tif']
    from scipy.ndimage import mean
    import tifffile
    

    # path = '/datajoint-data/data/jisooj/RN_OPI-1681_2023-02-15_scan9FGLEFJ3_sess9FGLEFJ3/suite2p_exp9FGLEFJ3/suite2p/plane0/reg_tif'
    # Get a list of all tiff files in the folder
    tiff_files = [os.path.join(path, f) for f in natsorted(os.listdir(path)) if f.endswith('.tif')]

    # print(tiff_files)

    # Load each tiff stack into a list of numpy arrays
    stacks = []
    for f in tiff_files:
        with tifffile.TiffFile(f) as tif:
            # Get the number of pages in the file
            num_pages = len(tif.pages)
            
            # Create a numpy array to store all pages
            stack = np.zeros((num_pages,) + tif.pages[0].shape, dtype=tif.pages[0].dtype)
            
            # Iterate over the pages and store them in the array
            for i, page in enumerate(tif.pages):
                stack[i] = page.asarray()

        stacks.append(stack)

    # Concatenate the stacks into a single numpy array along the z-axis
    volume = np.concatenate(stacks, axis=0)

    # delete registration tiff
    for f in tiff_files:
        os.remove(f) 
    
    ### moving average filter
    # Create a running Z mean projection of the volume

    runav = 10
    # running_z_projection = uniform_filter_mt(volume, size=(runav,xyrunav,xyrunav))
    running_z_projection = rolling_average_filter(volume, runav)

    session_id = curation_key['session_id']
    scan_id = curation_key['scan_id']

    filename = os.path.join(path, 'registered_movie_' + session_id + '_' + scan_id + '_' + str(runav) + '_frame_runningaverage2' + '.mp4')

    fps = 120   # frames per second - 120 default
    p1 = 2       # percentile scaling low - 1 default
    p2 = 99.998  # percentile scaling high - 99.995 default

    rescaled_image_8bit = make_stack_movie(running_z_projection, filename, fps, p1, p2)

    # return rescaled_image_8bit
    # tmpdir = dj.config['custom'].get('suite2p_fast_tmp')[0]


