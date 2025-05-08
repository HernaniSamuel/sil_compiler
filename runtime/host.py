# runtime/host.py

import pyopencl as cl
import numpy as np

class HostRuntime:
    def __init__(self):
        platforms = cl.get_platforms()
        if not platforms:
            raise Exception("Nenhuma plataforma OpenCL encontrada!")

        self.platform = platforms[0]
        self.device = self.platform.get_devices()[0]
        self.context = cl.Context([self.device])
        self.queue = cl.CommandQueue(self.context)

    def load_spirv(self, path):
        with open(path, 'rb') as f:
            binary = f.read()
        self.program = cl.Program(self.context, [self.device], [binary]).build()

    def create_buffer(self, np_array, flags=cl.mem_flags.READ_WRITE):
        mf = cl.mem_flags
        return cl.Buffer(self.context, flags | mf.COPY_HOST_PTR, hostbuf=np_array)

    def run_kernel(self, kernel_name, global_size, inputs):
        kernel = getattr(self.program, kernel_name)
        args = list(inputs.values())
        kernel.set_args(*args)
        cl.enqueue_nd_range_kernel(self.queue, kernel, (global_size,), None)

    def read_buffer(self, buf, dtype, shape):
        output = np.empty(shape, dtype=dtype)
        cl.enqueue_copy(self.queue, output, buf)
        self.queue.finish()
        return output

    def run_scalar(self, kernel_name: str, *scalar_args):
        """
        Chamada rápida para kernels sem buffers:
            rt.run_scalar("nome_kernel", arg0, arg1, ...)
        """
        kernel = getattr(self.program, kernel_name)
        if scalar_args:
            kernel.set_args(*scalar_args)
        # Executa uma única work‑item
        cl.enqueue_nd_range_kernel(self.queue, kernel, (1,), None)
        self.queue.finish()