from flask import Flask, send_file, render_template
from PIL import Image
import numpy as np
import io, sys, glob, os, time

class image_stack:
    def __init__(self,batchsize = 8):
        self.imagelist = []
        self.imnum = 0
        self.batchid = 0
        self.batchsize = batchsize

    def enqueue(self,im):
        self.imagelist.append(im)
        self.imnum+=1

    def loadim(self,id):
        idx = id + self.batchid*8
        if id == 7:
            self.batchid+=1
        return self.imagelist[idx]

    def loadfrompath(self,path):
        # filenames = sorted(glob.glob(os.path.join(path, '*.png')))
        filenames = glob.glob(os.path.join(path, '*.png'))
        for file_path in filenames:
            raw_data = Image.open(file_path)
            arr = np.array(raw_data)
            self.enqueue(arr)
            raw_data.close()


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
#
# raw_data = [
#     [[255,255,255],[0,0,0],[255,255,255]],
#     [[0,0,1],[255,255,255],[0,0,0]],
#     [[255,255,255],[0,0,0],[255,255,255]],
# ]


file_path="./temp"
imstact = image_stack()
imstact.loadfrompath(file_path)
raw_data = Image.open(file_path+"/000000.png")


@app.route('/refresh/', methods=['GET','POST'])
def test():
    value = request.args.get("value")
    print('Hello world !idx%s'%value, file=sys.stderr)

    if request.method == "POST":
      clicked=request.json['value']

    return render_template('gallery.html')




@app.route('/gallery')
def display_gallery():
    # my numpy array
    arr = np.array(raw_data)
    # convert numpy array to PIL Image
    img = Image.fromarray(arr.astype('uint8'))
    # create file-object in memory
    file_object = io.BytesIO()
    # write PNG in file-object
    img.save(file_object, 'PNG')
    # move to beginning of file so `send_file()` it will read from start
    file_object.seek(0)
    return render_template('gallery.html')

@app.route('/get_image/<int:idx>')
def image(idx):
    print('Hello world !idx%s'%idx, file=sys.stderr)
    # my numpy array
    arr = imstact.loadim(idx)
    print('Hello world !batch%s'%imstact.batchid, file=sys.stderr)
    img = Image.fromarray(arr.astype('uint8'))
    # create file-object in memory
    file_object = io.BytesIO()
    # write PNG in file-object
    img.save(file_object, 'PNG')
    # move to beginning of file so `send_file()` it will read from start
    file_object.seek(0)
    return send_file(file_object, mimetype='image/PNG')

if __name__ == '__main__':
   app.run(debug = True)
