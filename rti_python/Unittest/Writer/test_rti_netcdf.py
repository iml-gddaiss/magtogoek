from rti_python.Writer.rti_netcdf import RtiNetcdf


def test_netcdf():
    file_paths = [r"C:\Users\rico\Documents\data\Waves_5_beam\B0000006.ENS"]

    net_cdf = RtiNetcdf()
    net_cdf.export(file_paths[0], [0, 4096], 0.61)


def test_netcdf_1():
    file_path = r"C:\Users\rico\Documents\data\Vault\RTI_20200716172154_00932.bin"
    net_cdf = RtiNetcdf()
    net_cdf.export(file_path, [0, 205], 1.0)


def test_analyze_file():
    file_paths = [r"C:\Users\rico\Documents\data\Waves_5_beam\B0000006.ENS"]

    net_cdf = RtiNetcdf()
    results = net_cdf.analyze_file(file_paths[0])

    assert 4096 == results['EnsCount']
    assert 2048 == results['PrimaryEnsCount']
    assert 2048 == results['VerticalEnsCount']
    assert 2048 == results['EnsPairCount']


def test_analyze_file_1():
    file_paths = r"C:\Users\rico\Documents\data\Vault\RTI_20200716155302_00932.BIN"

    net_cdf = RtiNetcdf()
    results = net_cdf.analyze_file(file_paths)


def test_analyze_file_thread():
    file_paths = r"C:\Users\rico\Documents\data\Vault\RTI_20200716155302_00932.BIN"

    net_cdf = RtiNetcdf()
    results = net_cdf.analyze_file(file_paths)