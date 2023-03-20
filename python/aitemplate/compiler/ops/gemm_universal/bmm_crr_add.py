#  Copyright (c) Meta Platforms, Inc. and affiliates.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
"""
Batch GEMM specialization for A[ColMajor], B[RowMajor], C[RowMajor] with Add.
"""

from aitemplate.compiler.base import Tensor
from aitemplate.compiler.ops.gemm_universal import bmm_crr
from aitemplate.compiler.ops.gemm_universal.bmm import is_valid_inputs
from aitemplate.compiler.tensor_accessor import TensorAccessor

# pylint: disable=C0103, W0223


class bmm_crr_add(bmm_crr):
    """Batch GEMM specialization for A[ColMajor], B[RowMajor], C[RowMajor] with Add.
    C can be the same size as the output or be broadcast as bias.

    This operator is equivalent to the following PyTorch code:

    .. highlight:: python
    .. code-block:: python

        X_pt = torch.randn(B, K, M).cuda().half()
        W_pt = torch.randn(B, K, N).cuda().half()
        D_pt = torch.randn(B, M, N).cuda().half()

        XT = torch.transpose(X_pt, 2, 1)
        Y_pt = torch.bmm(XT, W_pt)
        Y_pt = Y_pt + D_pt

    """

    def __init__(self):
        """Constructor for bmm_crr_add"""
        super().__init__()
        self._attrs["op"] = "bmm_crr_add"
        self._attrs["has_d"] = True

    @staticmethod
    def is_valid_inputs(A: Tensor, B: Tensor, C: Tensor):
        output_shapes = bmm_crr()._infer_shapes(A, B)
        c_shapes = C.shape()
        return is_valid_inputs(output_shapes, c_shapes)

    def __call__(self, a: Tensor, b: Tensor, c: Tensor) -> Tensor:
        """Call bmm_crr_add with tensors a, b, c

        Equivalent to the following PyTorch code:

        .. highlight:: python
        .. code-block:: python

            y = bmm(a.transpose(2, 1), b) + c

        Parameters
        ----------
        a : Tensor
            Tensor in shape (B, K, M)
        b : Tensor
            Tensor in shape (B, K, N)
        c : Tensor
            Tensor in shape (B, M, N)

        Returns
        -------
        Tensor
            Tensor in shape (B, M, N)
        """
        output = super().__call__(a, b)
        self._attrs["inputs"].append(c)
        self._attrs["input_accessors"] = [
            TensorAccessor(tensor) for tensor in self._attrs["inputs"]
        ]
        self._set_depth()
        return output