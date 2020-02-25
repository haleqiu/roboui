from flask import Flask, send_file, render_template, request, redirect, url_for
from PIL import Image
import numpy as np
import io, sys, glob, os, time

class image_stack:
    def __init__(self,batchsize = 8):
        self.imagelist = []
        self.imnum = 0
        self.image_id = -1
        self.batchid = 0
        self.batchsize = batchsize

    def enqueue(self,im):
        self.imagelist.append(im)
        self.imnum+=1

    def loadim(self,id):
        idx = id + self.batchid*self.batchsize
        if id == self.batchsize-1:
            self.batchid+=1
        return self.imagelist[idx]

    def request_image(self,id):
    ## the simulated API
        idx = int(id)
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

file_path="./temp"
imstact = image_stack(batchsize=1)
imstact.loadfrompath(file_path)

@app.route('/refresh/')
def refresh_image():
    return redirect(url_for('display_gallery'))

@app.route('/select', methods=['GET','POST'])
def select_image():
    value = request.args.get("idx")
    print('select !idx%s'%value, file=sys.stderr)
    return "200"

@app.route('/gallery')
def display_gallery():
    return render_template('anigallery.html',idx1="0")

@app.route('/get_image/<int:idx>')
def image(idx):
    print('Hello world !idx%s'%idx, file=sys.stderr)
    # my numpy array
    # arr = imstact.loadim(idx)
    arr = imstact.request_image(idx)
    print('Hello world !batch%s'%imstact.batchid, file=sys.stderr)
    img = Image.fromarray(arr.astype('uint8'))
    # create file-object in memory
    file_object = io.BytesIO()
    # write PNG in file-object
    img.save(file_object, 'PNG')
    print(arr,file=sys.stderr)
    # move to beginning of file so `send_file()` it will read from start
    file_object.seek(0)
    return send_file(file_object, mimetype='image/PNG')

if __name__ == '__main__':
   app.run(debug = True)
