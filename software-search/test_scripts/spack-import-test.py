import spack

def main():
    spc = spack.spec.Spec('laghos@3.1%intel@19.0.4.227 ^openmpi@3.0.1')
    print("Success!")
