# Graded Motor Imagery - Left/Right Discrimination Therapy
Interactive program for performing left/right discrimination treatments for graded motor imagery

## Usage

```
python gmi.py [options]
```

```
optional arguments:
  -h, --help            show this help message and exit
  --size W,H            screen size of the form W,H (default: 800,600)
  --limit CHOICE        limit to either 'hands' or 'feet' (default None)
  -o PATH, --out PATH   file to record outputs to
  -c NUM, --count NUM   limit number of images to NUM (default 30)
  -v, --verbose         be verbose about operations performed
```

```
python analysis.py [options] <file>
```

```
positional arguments:
  file                 file to analyze

optional arguments:
  -h, --help           show this help message and exit
  --csv FILE           write summary CSV to FILE
  -a, --append         append to CSV file; do not overwrite
  --detailed-csv FILE  write each test to N_FILE, N = 1, 2, 3, ...
```

## Assets
Assets are stored in directories
    ```
    assets/hands/left
    ```
    ,
    ```
    assets/hands/right
    ```
    ,
    ```
    assets/feet/left
    ```
    , and
    ```
    assets/feet/right
    ```
Any directories not existing are created on first run, and all common image formats are supported, including PNG and JPEG.

The folder structure is incredibly important. Images MUST be in one of the four directories above. Classifications are either ```hands``` or ```feet```, and the direction must be either ```left``` or ```right```.

All of this information is used for the statistical analysis part of the application

## Analysis
Using
```
analysis.py
```
useful results can be deduced from the main program's output log.

## Assets provided
Sample assets are provided from the following resources:

```assets/feet/right/free_shoe1.png``` from ```https://www.pexels.com/photo/foot-brown-shoe-2491/```
    scaled to 800 pixels wide

## Analysis

Work in progress

Use ```--out <PATH>``` to append results to the file designated by <PATH> in CSV format. Using ```--analyze <FILE>``` to analyze the file and get statistical information about it.

## References

