import h5py

from module.H5File import H5File


class Material(H5File):
    def __init__(self):
        super(Material, self).__init__()

    def create(self, grp, name, dct):
        """Create New Material.

        :return:
        """
        gp = self.fh.require_group(grp)
        mat = gp.require_group(name)
        for i in dct:
            if i in mat:
                del mat[i]

            if isinstance(dct[i], str):
                dt = h5py.special_dtype(vlen=str)
                mt = mat.create_dataset(i, (1,), dtype=dt)
                mt[0] = dct[i]
            else:
                mat.create_dataset(
                    i,
                    data=dct[i]
                )
