import gradio as gr
import random
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
import cv2
import numpy as np
from multiprocessing import Pool, cpu_count
import warnings
warnings.filterwarnings("ignore")

def new_array(size, numRange):
    if numRange<=0:
        # generate random non repeating list starting from 1
        arr = [i+1 for i in range(size)]
        random.shuffle(arr)
        return arr
    else:
        # generate random repeating list from 1 to numRange
        return [random.randint(1, numRange) for i in range(size)]
    
def swap(arr, index1, index2):
    # swap 2 elements in a list
    arr[index1], arr[index2] = arr[index2], arr[index1]

def quicksort(arr, ascending, leftBound=None, rightBound=None):
    if leftBound is None or rightBound is None:
        leftBound = 0
        rightBound = len(arr)-1
        steps.append([arr[:], leftBound, rightBound, -1, -1, "start", [-1, -1, -1], 1]) # store step -----
    else:
        steps.append([arr[:], leftBound, rightBound, -1, -1, "new sublist", [-1, -1, -1], steps[-1][-1]+1]) # store step -----

    # base case
    if rightBound-leftBound<1:
        return

    # get middle element
    mid = (rightBound+leftBound)//2

    # get median of three
    l = arr[leftBound]
    m = arr[mid]
    r = arr[rightBound]
    if (l < m < r) or (r < m < l):
        pivotIndex = mid
    elif (m < l < r) or (r < l < m):
        pivotIndex = leftBound
    else:
        pivotIndex = rightBound

    steps.append([arr[:], leftBound, rightBound, -1, -1, "get left, middle, and right elements", [leftBound, mid, rightBound], steps[-1][-1]]) # store step -----
    steps.append([arr[:], leftBound, rightBound, -1, -1, "get median of three for pivot", [pivotIndex, -1, -1], steps[-1][-1]]) # store step -----
    
    swap(arr, rightBound, pivotIndex)

    steps.append([arr[:], leftBound, rightBound, -1, -1, "move pivot to right", [rightBound, -1, -1], steps[-1][-1]]) # store step -----

    # left and right pointers
    left = leftBound
    right = rightBound-1

    steps.append([arr[:], leftBound, rightBound, left, right, "initialize left and right pointers", [rightBound, -1, -1], steps[-1][-1]]) # store step -----

    while left<right:
        # move left pointer
        while ((ascending and arr[left]<=arr[rightBound]) or (not ascending and arr[left]>=arr[rightBound])) and left<right:
            left+=1
            steps.append([arr[:], leftBound, rightBound, left, right, "move left pointer", [rightBound, -1, -1], steps[-1][-1]]) # store step -----

        # more right pointer
        while ((ascending and arr[right]>=arr[rightBound]) or (not ascending and arr[right]<=arr[rightBound])) and left<right:
            right-=1
            steps.append([arr[:], leftBound, rightBound, left, right, "move right pointer", [rightBound, -1, -1], steps[-1][-1]]) # store step -----

        swap(arr, left, right)
        steps.append([arr[:], leftBound, rightBound, left, right, "swap left and right pointer", [rightBound, -1, -1], steps[-1][-1]]) # store step -----

    # move pivot back
    if (ascending and arr[right]>arr[rightBound]) or (not ascending and arr[right]<arr[rightBound]):
        swap(arr, rightBound, right)
        steps.append([arr[:], leftBound, rightBound, left, right, "swap pivot and right pointer", [rightBound, -1, -1], steps[-1][-1]]) # store step -----

    # quicksort on the 2 sub lists
    quicksort(arr, ascending, leftBound, right)
    quicksort(arr, ascending, right+1, rightBound)

# GUI ------------------------------------------------------------

outputFilepath = "output.mp4"

def draw_step(stepIndex, stepsCopy):
    arr, leftBound, rightBound, left, right, stepText, pivotIndex, calls = stepsCopy[stepIndex]

    # set colors of bars
    colors = []
    for i in range(len(arr)):
        if stepIndex >= len(stepsCopy)-1:
            colors.append("green")
        elif i==pivotIndex[0] or i==pivotIndex[1] or i==pivotIndex[2]:
            colors.append("red")
        elif i==left and i==right:
            colors.append("brown")
        elif i==left:
            colors.append("orange")
        elif i==right:
            colors.append("blue")
        else:
            colors.append("white")
    
    # make bar graph
    fig, ax = plt.subplots()
    fig.patch.set_facecolor('black')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.bar(range(len(arr)), arr, color=colors)
    ax.set_facecolor("black")
    ax.set_title("Calls " + str(calls) + "     Steps " + str(stepIndex) + "\n" + stepText, color="white")

    # make leftBound and rightBound lines
    if leftBound != -1:
        ax.axvline(x=leftBound-0.5, color="red", linestyle="solid", linewidth=2)
        ax.axvline(x=rightBound+0.5, color="red", linestyle="solid", linewidth=2)

    # save plot as image (https://stackoverflow.com/questions/57316491/how-to-convert-matplotlib-figure-to-pil-image-object-without-saving-image)
    buf = BytesIO()
    fig.savefig(buf)
    buf.seek(0)
    plt.close()
    return Image.open(buf)

def render_sort(size, numRange, ascending, fps):
    # reset program with new list and sort
    global steps
    steps = []
    arr = new_array(size, numRange)
    quicksort(arr, ascending)
    steps.append([arr[:], -1, -1, -1, -1, "sorted", [-1, -1, -1], steps[-1][-1]]) # store step -----

    # multiprocessing to draw steps (https://stackoverflow.com/questions/44660676/python-using-multiprocessing)
    results = []
    pool = Pool(processes=(cpu_count() - 1))
    for i in range(len(steps)):
        result = pool.apply_async(draw_step, args=(i,steps))
        results.append(result)
    pool.close()
    pool.join()

    # get images from multiprocessing results
    stepImages = []
    for i in range(len(steps)):
        stepImages.append(results[i].get())

    # generate video (https://stackoverflow.com/questions/52414148/turn-pil-images-into-video-on-linux)
    videodims = (640,480)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')    
    video = cv2.VideoWriter(outputFilepath,fourcc, fps,videodims)
    for img in stepImages:
        video.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))

    video.release()

    return outputFilepath

def returnInput(input):
    return input

with gr.Blocks() as demo:
    video = gr.Video(width=640, height=480)

    # variables
    fps = gr.State(10)
    size = gr.State(10)
    numRange = gr.State(0)
    ascending = gr.State(True)

    # ui
    fpsSlider = gr.Slider(label="FPS", minimum=1, maximum=120, step=1, value=10)
    sizeSlider = gr.Slider(label="Array Size", minimum=0, maximum=100, step=1, value=10)
    numRangeSlider = gr.Slider(label="Range of Numbers (0 for no repeat)", minimum=0, maximum=100, step=1, value=0)
    ascendingCheckBox = gr.Checkbox(label="Ascending", value=True)
    renderButton = gr.Button("Render Sort")

    # fps slider
    fpsSlider.release(
        fn=returnInput,
        inputs=fpsSlider,
        outputs=fps,
        show_progress=False
    )

    # sort settings
    sizeSlider.release(
        fn=returnInput,
        inputs=sizeSlider,
        outputs=size,
        show_progress=False
    )

    numRangeSlider.release(
        fn=returnInput,
        inputs=numRangeSlider,
        outputs=numRange,
        show_progress=False
    )

    ascendingCheckBox.change(
        fn=returnInput,
        inputs=ascendingCheckBox,
        outputs=ascending,
        show_progress=False
    )

    # render sort
    renderButton.click(
        fn=render_sort,
        inputs=[size, numRange, ascending, fps],
        outputs=video,
        show_progress=True
    )

if __name__ == "__main__":
    demo.launch()

