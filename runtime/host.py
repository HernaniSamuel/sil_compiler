# runtime/host.py

import pyopencl as cl
import numpy as np

class HostRuntime:
    def __init__(self):
        # Cria contexto e fila de comandos
        platforms = cl.get_platforms()
        if not platforms:
            raise Exception("Nenhuma plataforma OpenCL encontrada!")

        self.platform = platforms[0]
        self.device = self.platform.get_devices()[0]
        self.context = cl.Context([self.device])
        self.queue = cl.CommandQueue(self.context)

    def load_spirv(self, spirv_file_path):
        # Carrega SPIR-V binário
        with open(spirv_file_path, 'rb') as f:
            spirv_binary = f.read()

        self.program = cl.Program(self.context, [self.device], [spirv_binary]).build()

    def create_buffer(self, np_array, flags=cl.mem_flags.READ_WRITE):
        # Cria buffer associado a um numpy array
        mf = cl.mem_flags
        buf = cl.Buffer(self.context, flags | mf.COPY_HOST_PTR, hostbuf=np_array)
        return buf

    def run_kernel(self, kernel_name, global_size, *args):
        # Executa kernel
        kernel = getattr(self.program, kernel_name)
        kernel.set_args(*args)
        cl.enqueue_nd_range_kernel(self.queue, kernel, (global_size,), None)

    def read_buffer(self, buf, dtype, shape):
        # Lê buffer de volta para numpy array
        result = np.empty(shape, dtype=dtype)
        cl.enqueue_copy(self.queue, result, buf)
        self.queue.finish()
        return result

if __name__ == "__main__":
    # Exemplo de uso
    rt = HostRuntime()

    # Assume que output.spv já foi gerado
    rt.load_spirv("../output.spv")

    # Cria dados de entrada
    a_np = np.array([25], dtype=np.uint32)
    b_np = np.array([32], dtype=np.uint32)
    out_np = np.array([0], dtype=np.uint32)

    # Cria buffers
    a_buf = rt.create_buffer(a_np)
    b_buf = rt.create_buffer(b_np)
    out_buf = rt.create_buffer(out_np)

    # Executa kernel
    rt.run_kernel("main", 1, a_buf, b_buf, out_buf)

    # Lê o resultado
    result = rt.read_buffer(out_buf, np.uint32, (1,))

    print("Resultado:", result[0])
