# Graded Motor Imagery - Left/Right Discrimination Therapy
Interactive program for performing left/right discrimination treatments for graded motor imagery

## Usage

```python main.py [options]```

```
optional arguments:
  -h, --help            show this help message and exit
  -p [PATHS [PATHS ...]], --paths [PATHS [PATHS ...]]
                        load images from PATHS (default: ./assets/*)
  -o PATH, --out PATH   file to record outputs to
  -c NUM, --count NUM   limit number of images to NUM (default 30)
  --repeats             allow repeats
  --analyze FILE        analyze FILE and exit
  -v, --verbose         be verbose about operations performed
```

## Assets
Assets are stored in directories
    ```assets/hands/left```, ```assets/hands/right```, ```assets/feet/left```, and ```assets/feet/right```
Any directories not existing are created on first run, and all common image formats are supported, including PNG and JPEG.

## Assets provided
Sample assets are provided from the following resources:

```assets/feet/right/free_shoe1.png``` from ```https://www.pexels.com/photo/foot-brown-shoe-2491/```
    scaled to 800 pixels wide
