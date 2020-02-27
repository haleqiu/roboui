#!/usr/bin/env python3

# Copyright <2019> <Chen Wang [https://chenwang.site], Carnegie Mellon University>

# Redistribution and use in source and binary forms, with or without modification, are 
# permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this list of 
# conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice, this list 
# of conditions and the following disclaimer in the documentation and/or other materials 
# provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors may be 
# used to endorse or promote products derived from this software without specific prior 
# written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY 
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES 
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT 
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED 
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; 
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN 
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH 
# DAMAGE.


import cv2
import rospy
import torch
import torchvision
import io, os, sys
import numpy as np
from rosutil import ROSArgparse
from interestingness_ros.msg import InterestInfo
from interaction.srv import Interest, InterestRequest
from flask import Flask, send_file, render_template, request, redirect, url_for
from PIL import Image

class InteractionClient:
    def __init__(self, args):
        super(InteractionClient, self).__init__()
        rospy.logwarn('Waiting for interaction services')
        rospy.wait_for_service('interaction')
        self.images = None
        self.ids = None
        self.imagedict = {}
        self.service = rospy.ServiceProxy('interaction', Interest)

    def request_images(self, id=0):
        #this method request for new images and save to a public value
        print('request!idx: %d'%id, file=sys.stderr)
        res = self.service([id])
        rospy.loginfo('Service call successed!')
        self.ids = res.ids 
        
        images = torch.Tensor(res.images).view(res.images_shape)
        self.images = [i.transpose(1,2,0) for i in images.numpy()]
        for i in range(np.shape(self.ids)[0]):
            self.imagedict.update({self.ids[i]:self.images[i]})
        # print(self.imagedict, file=sys.stderr)

    def load_image(self, id):
        # take the image from the image dict
        # print(self.imagedict[id].shape,file=sys.stderr)
        return self.imagedict[id]

    def spin(self):
        while not rospy.is_shutdown():
            self.callback()

    def callback(self):
        try:
            res = self.service([0])
            rospy.loginfo('Service call successed!')
            print('res.ids:', res.ids)
            images = torch.Tensor(res.images).view(res.images_shape)
            show_batch_origin(images)
        except(rospy.ServiceException):
            rospy.logwarn("Service call failed!")


def show_batch_origin(batch, name='video', waitkey=1):
    grid = torchvision.utils.make_grid(batch).cpu()
    img = grid.numpy()[::-1].transpose((1, 2, 0))
    cv2.imshow(name, img)
    cv2.waitKey(waitkey)
    return img


if __name__ == '__main__':
    rospy.init_node('interaction_client')
    parser = ROSArgparse(relative='interaction_client/')
    args = parser.parse_args()
    client = InteractionClient(args)
    res =  client.service([0])
    images = torch.Tensor(res.images).view(res.images_shape)
    
    app = Flask(__name__)
    # @app.route('/gallery')
    # def display_gallery():
    #     return render_template('gallery.html',idx1="0")

    @app.route('/gallery')
    def display_gallery():
        if client.images == None:
            client.request_images(0)
        idxlist = list(client.ids)
        print(idxlist, file=sys.stderr)
        return render_template('anigallery.html',idxlist=idxlist)

    @app.route('/get_image/<int:idx>')
    def image(idx):
        print('Hello world !idx%s'%idx, file=sys.stderr)
        # my numpy array
        # arr = imstact.loadim(idx)
        arr = client.load_image(idx)
        img = Image.fromarray((arr*255).astype('uint8'))
        # create file-object in memory
        file_object = io.BytesIO()
        # write PNG in file-object
        img.save(file_object, 'PNG')
        # move to beginning of file so `send_file()` it will read from start
        file_object.seek(0)
        return send_file(file_object, mimetype='image/PNG')

    @app.route('/select', methods=['GET','POST'])
    def select_image():
        value = request.args.get("idx")
        print('select !idx%s'%value, file=sys.stderr)

        client.request_images(int(value))
        return "200"

    @app.route('/refresh/')
    def refresh_image():
        client.request_images(0)
        return redirect(url_for('display_gallery'))

    app.run()
    #app.run(host=os.getenv('IP','0,0,0,0'),port=int(os.getenv('PORT','4444')))
    client.spin()
