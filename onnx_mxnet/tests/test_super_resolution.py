# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#     http://www.apache.org/licenses/LICENSE-2.0
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

from __future__ import absolute_import as _abs
import mxnet as mx
import numpy as np
import os
import onnx_mxnet
from collections import namedtuple

# load protobuf format
def _as_abs_path(fname):
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(cur_dir, fname)

# download test image
def download(url, path, overwrite=False):
    import urllib2, os
    if os.path.exists(path) and not overwrite:
        return
    print('Downloading {} to {}.'.format(url, path))
    with open(path, 'w') as f:
        f.write(urllib2.urlopen(url).read())

model_url = 'https://s3.amazonaws.com/onnx-mxnet/examples/super_resolution.onnx'

download(model_url, 'super_resolution.onnx')

print "Converting onnx format to mxnet's symbol and params..."
sym, params = onnx_mxnet.import_model('super_resolution.onnx')

# Load test image
from PIL import Image
input_image_dim=224
output_image_dim=672
img_url = 'https://s3.amazonaws.com/onnx-mxnet/examples/super_res_input.jpg'
download(img_url, 'super_res_input.jpg')
img = Image.open('super_res_input.jpg').resize((input_image_dim, input_image_dim))
img_ycbcr = img.convert("YCbCr")
img_y, img_cb, img_cr = img_ycbcr.split()
x = np.array(img_y)[np.newaxis, np.newaxis, :, :]

# create module
mod = mx.mod.Module(symbol=sym, data_names=['input_0'], label_names=None)
mod.bind(for_training=False, data_shapes=[('input_0',x.shape)])
mod.set_params(arg_params=params, aux_params=None)

# run inference
Batch = namedtuple('Batch', ['data'])
mod.forward(Batch([mx.nd.array(x)]))

# Save the result
img_out_y = Image.fromarray(np.uint8(mod.get_outputs()[0][0][0].asnumpy().clip(0, 255)), mode='L')

result_img = Image.merge(
    "YCbCr", [
            img_out_y,
            img_cb.resize(img_out_y.size, Image.BICUBIC),
            img_cr.resize(img_out_y.size, Image.BICUBIC)
    ]).convert("RGB")
result_img.save("super_res_output.jpg")
