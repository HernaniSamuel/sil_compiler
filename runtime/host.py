# runtime/host.py

import pyopencl as cl
import numpy as np


class HostRuntime:
    """
    A simple OpenCL runtime wrapper for running SPIR-V kernels
    from Python using PyOpenCL.

    Provides helpers for:
    - Creating buffers
    - Loading SPIR-V binaries
    - Executing kernels with or without buffers
    - Reading back data from device
    """

    def __init__(self):
        # Select the first available OpenCL platform and device
        platforms = cl.get_platforms()
        if not platforms:
            raise Exception("No OpenCL platforms found!")

        self.platform = platforms[0]
        self.device = self.platform.get_devices()[0]

        # Create OpenCL context and command queue
        self.context = cl.Context([self.device])
        self.queue = cl.CommandQueue(self.context)

    def load_spirv(self, path):
        """
        Load and build a SPIR-V binary from a file.

        Args:
            path (str): Path to a compiled .spv file.
        """
        with open(path, 'rb') as f:
            binary = f.read()

        self.program = cl.Program(self.context, [self.device], [binary]).build()

    def create_buffer(self, np_array, flags=cl.mem_flags.READ_WRITE):
        """
        Create a buffer from a NumPy array and upload it to device.

        Args:
            np_array (np.ndarray): The host array to copy to device.
            flags (OpenCL flags): Optional memory flags.

        Returns:
            cl.Buffer: A buffer object ready to be passed to a kernel.
        """
        mf = cl.mem_flags
        return cl.Buffer(self.context, flags | mf.COPY_HOST_PTR, hostbuf=np_array)

    def run_kernel(self, kernel_name, global_size, inputs):
        """
        Run a kernel with the given input buffers.

        Args:
            kernel_name (str): The kernel function name.
            global_size (int): Number of work-items to launch.
            inputs (dict): A mapping of parameter names to cl.Buffer objects.
        """
        kernel = getattr(self.program, kernel_name)
        args = list(inputs.values())
        kernel.set_args(*args)

        cl.enqueue_nd_range_kernel(self.queue, kernel, (global_size,), None)

    def read_buffer(self, buf, dtype, shape):
        """
        Read data from a device buffer into a NumPy array.

        Args:
            buf (cl.Buffer): The buffer to read from.
            dtype (np.dtype): The data type (e.g., np.uint32).
            shape (tuple): The shape of the output array.

        Returns:
            np.ndarray: The host-side result.
        """
        output = np.empty(shape, dtype=dtype)
        cl.enqueue_copy(self.queue, output, buf)
        self.queue.finish()
        return output

    def run_scalar(self, kernel_name, *scalar_args):
        """
        Shortcut for running kernels that only take scalar values (no buffers).

        Example:
            rt.run_scalar("my_kernel", 42, 7.5)

        Args:
            kernel_name (str): The kernel function name.
            *scalar_args: Positional scalar arguments.
        """
        kernel = getattr(self.program, kernel_name)
        if scalar_args:
            kernel.set_args(*scalar_args)

        cl.enqueue_nd_range_kernel(self.queue, kernel, (1,), None)
        self.queue.finish()

    def run(self, kernel_name, *args):
        """
        Run a kernel with any positional arguments (scalar or buffer).

        Args:
            kernel_name (str): The kernel function name.
            *args: Positional arguments to pass to the kernel.
        """
        kernel = getattr(self.program, kernel_name)
        kernel.set_args(*args)

        cl.enqueue_nd_range_kernel(self.queue, kernel, (1,), None)
        self.queue.finish()
