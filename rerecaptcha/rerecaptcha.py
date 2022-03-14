import base64
import io
import os

import numpy as np
import pytesseract
import re

from PIL import Image, ImageChops, ImageOps
import requests
# utflag{skibidi_bop_mm_dada_uLG7Jrd5hP}
rawa = """
a
b
0
"""
lastSession, lastCode, lastCount = rawa.split()
lastCount = int(lastCount)
begin = """<html>
  <head>
    <link rel="stylesheet" href="/static/styles.css">
    <title>Are u a bot</title>
  </head>
  <body>
    <div>
      <h1>ReReCaptcha</h1>
      <p>You have solved """
middle = """ captchas in a row correctly!</p>
      <img style="width: 500px" src="data:image/png;base64, """
end = """"><br>
      <form method="post">
        
        <input type="text" name="solution" placeholder="solution">
        <input type="submit">
      </form>
    </div>
  </body>
</html>"""

dump = []
for i in os.listdir("letters"):
    dump.append([np.array(ImageOps.grayscale(Image.open("letters/" + i))).astype(np.int16), i[:-4]])
for i in os.listdir("lett1"):
    dump.append([np.array(ImageOps.grayscale(Image.open("lett1/" + i))).astype(np.int16), i[:-4]])


def getNearestLetter(imgArray):
    for l in dump:
        if imgArray.shape == l[0].shape:
            if not ((np.absolute(imgArray.astype(np.int16) - l[0]) > 50).any()):
                return l[1]
    Image.fromarray(imgArray).save("err.png")
    raise Exception("unknown letter")


def getLetters(resultImage):
    dataResult = np.array(resultImage)
    dataResult = crop(dataResult)
    code = ""
    while dataResult.shape[1] > 0:
        letter, dataResult = splitLetter(dataResult)
        if letter.shape[1] == 0:
            code += getNearestLetter(dataResult)
            break
        code += getNearestLetter(letter)
    return code


def main():
    f = open("hist", "a+")
    global lastSession, lastCode, lastCount
    orig = Image.open("index.png").convert("RGB")
    k = 0
    j = 0
    while True:
        response = requests.request("POST", "http://web1.utctf.live:7132/", cookies={
            "session": lastSession
        }, data={"solution": lastCode})
        lastSession = response.cookies.get("session")
        page = response.content.decode("utf-8")
        if not page.startswith(begin + str(lastCount) + middle) or not page.endswith(end):
            print(page)
            f.write(page)
            f.write("\n")
        based = page.split("data:image/png;base64,")[1]
        based = based.split("\"")[0].strip()
        imageFile = base64.standard_b64decode(based)
        image = Image.open(io.BytesIO(imageFile)).convert("RGB")
        image.save("base" + str(k) + ".png")
        k += 1
        k %= 10
        dataOrig = np.array(orig)
        dataImage = np.array(image)
        result = np.bitwise_xor(dataOrig, dataImage)
        resultImage = ImageOps.grayscale(Image.fromarray(result))
        resultImage.save("result" + str(j) + ".png")
        j += 1
        j %= 10
        lastCode = getLetters(resultImage)
        lastCount += 1
        print(lastSession)
        print(lastCode)
        print(lastCount)
        print("-----------")
        f.write(str(lastSession) + "\n")
        f.write(str(lastCode) + "\n")
        f.write(str(lastCount) + "\n")
        f.write("-----------" + "\n")


def findFirstWhiteCol(image):
    for j in range(image.width):
        for i in range(image.height):
            if isWhile(image.getpixel([j, i])):
                return j
    else:
        return -1


def findFirstBlackCol(image):
    for j in range(image.width):
        for i in range(image.height):
            if not isBlack(image.getpixel([j, i])):
                break
        else:
            return j
    else:
        return -1


def findFirstWhiteRow(image):
    for i in range(image.height):
        for j in range(image.width):
            if isWhile(image.getpixel([j, i])):
                return j
    else:
        return -1


def findFirstBlackRow(image):
    for i in range(image.height):
        for j in range(image.width):
            if not isBlack(image.getpixel([j, i])):
                break
        else:
            return i
    else:
        return -1


def isBlack(d):
    return d[0] <= 100


def isWhile(d):
    return d[0] >= 170


def crop(dataResult):
    m, n = dataResult.shape
    if n == 0:
        return dataResult
    mask = dataResult > 170
    colMask = mask.any(0)
    rowMask = mask.any(1)
    colStart = colMask.argmax()
    colEnd = n - colMask[::-1].argmax()
    rowStart = rowMask.argmax()
    rowEnd = m - rowMask[::-1].argmax()
    return dataResult[rowStart:rowEnd, colStart:colEnd]


def splitLetter(dataResult):
    mask = dataResult > 170
    colMask = mask.any(0)
    m, n = dataResult.shape
    cropped = dataResult[0:m, 0:colMask.argmin()]
    result = dataResult[0:m, colMask.argmin():n]
    return crop(cropped), crop(result)


if __name__ == '__main__':
    main()
