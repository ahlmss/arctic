import pytest
from mock import patch, call
from pandas.testing import assert_frame_equal

from arctic import arctic as m
from arctic.scripts import arctic_copy_data as mcd
from ...util import read_str_as_pandas, run_as_main


@pytest.fixture(scope='function', autouse=True)
def init(arctic):
    arctic.initialize_library('user.library', m.VERSION_STORE, segment='month')
    arctic.initialize_library('user.library2', m.VERSION_STORE, segment='month')


ts = read_str_as_pandas("""             times | near
                   2012-09-08 17:06:11.040 |  1.0
                   2012-10-08 17:06:11.040 |  2.0
                   2012-10-09 17:06:11.040 |  2.5
                   2012-11-08 17:06:11.040 |  3.0""")
ts1 = read_str_as_pandas("""         times | near
                   2012-09-08 17:06:11.040 |  4.0
                   2012-10-08 17:06:11.040 |  5.0
                   2012-10-09 17:06:11.040 |  6.5
                   2012-11-08 17:06:11.040 |  7.0""")
ts2 = read_str_as_pandas("""         times | near
                   2012-10-08 17:06:11.040 |  5.0
                   2012-10-09 17:06:11.040 |  6.5""")
ts3 = read_str_as_pandas("""         times | near
                   2012-09-08 17:06:11.040 |  1.0
                   2012-10-08 17:06:11.040 |  5.0
                   2012-10-09 17:06:11.040 |  6.5
                   2012-11-08 17:06:11.040 |  3.0""")

def test_copy_data_no_force(arctic, mongo_host):
    src = 'user.library'
    dest = 'user.library2'
    # Put ts, ts1 in library
    arctic[src].write('some_ts', ts1)
    arctic[src].write('some_ts1', ts1)

    # Put some other value for ts in library2
    arctic[dest].write('some_ts', ts)

    # Create the user against the current mongo database
    src_host = 'arctic_' + src + '@' + mongo_host
    dest_host = 'arctic_' + dest + '@' + mongo_host
    with patch('arctic.scripts.arctic_copy_data.logger') as logger:
        run_as_main(mcd.main, '--src', src_host, '--dest', dest_host, '--log', 'CR101', 'some_ts', 'some_ts1')

    assert_frame_equal(ts, arctic[dest].read('some_ts').data)
    assert_frame_equal(ts1, arctic[dest].read('some_ts1').data)
    assert logger.info.call_args_list == [call('Copying data from %s -> %s' % (src_host, dest_host)),
                                          call('Copying: 2 symbols')]
    assert logger.warn.call_args_list == [call('Symbol: some_ts already exists in %s, use --force to overwrite or --splice to join with existing data' % dest_host)]
    assert arctic[dest].read_audit_log('some_ts1')[0]['message'] == 'CR101'


def test_copy_data_force(arctic, mongo_host):
    src = 'user.library'
    dest = 'user.library2'
    # Put ts, ts1 in library
    arctic[src].write('some_ts', ts)
    arctic[src].write('some_ts1', ts1)

    # Put some other value for ts in library2
    arctic[dest].write('some_ts', ts1)

    # Create the user against the current mongo database
    src_host = src + '@' + mongo_host
    dest_host = dest + '@' + mongo_host
    with patch('arctic.scripts.arctic_copy_data.logger') as logger:
        run_as_main(mcd.main, '--src', src_host, '--dest', dest_host, '--log', 'CR101', '--force', 'some_ts', 'some_ts1')

    assert_frame_equal(ts, arctic[dest].read('some_ts').data)
    assert_frame_equal(ts1, arctic[dest].read('some_ts1').data)
    assert logger.info.call_args_list == [call('Copying data from %s -> %s' % (src_host, dest_host)),
                                          call('Copying: 2 symbols')]
    assert logger.warn.call_args_list == [call('Symbol: some_ts already exists in destination, OVERWRITING')]
    assert arctic[dest].read_audit_log('some_ts1')[0]['message'] == 'CR101'


def test_copy_data_splice(arctic, mongo_host):
    src = 'user.library'
    dest = 'user.library2'
    # Put ts, ts1 in library
    arctic[src].write('some_ts', ts2)
    arctic[src].write('some_ts1', ts1)

    # Put some other value for ts in library2
    arctic[dest].write('some_ts', ts)

    # Create the user against the current mongo database
    src_host = src + '@' + mongo_host
    dest_host = dest + '@' + mongo_host
    with patch('arctic.scripts.arctic_copy_data.logger') as logger:
        run_as_main(mcd.main, '--src', src_host, '--dest', dest_host, '--log', 'CR101', '--splice', 'some_ts', 'some_ts1')

    assert_frame_equal(ts3, arctic[dest].read('some_ts').data)
    assert_frame_equal(ts1, arctic[dest].read('some_ts1').data)
    assert logger.info.call_args_list == [call('Copying data from %s -> %s' % (src_host, dest_host)),
                                          call('Copying: 2 symbols')]
    assert logger.warn.call_args_list == [call('Symbol: some_ts already exists in destination, splicing in new data')]

    assert arctic[dest].read_audit_log('some_ts')[0]['message'] == 'CR101'


def test_copy_data_wild(arctic, mongo_host):
    src = 'user.library'
    dest = 'user.library2'
    # Put ts, ts1 in library
    arctic[src].write('some_a_ts', ts)
    arctic[src].write('some_a_ts1', ts1)
    arctic[src].write('some_b_ts1', ts1)
    arctic[src].write('some_c_ts1', ts1)

    # Create the user against the current mongo database
    src_host = 'arctic_' + src + '@' + mongo_host
    dest_host = 'arctic_' + dest + '@' + mongo_host
    with patch('arctic.scripts.arctic_copy_data.logger') as logger:
        run_as_main(mcd.main, '--src', src_host, '--dest', dest_host, '--log', 'CR101', '.*_a_.*', '.*_b_.*')

    assert_frame_equal(ts, arctic[dest].read('some_a_ts').data)
    assert_frame_equal(ts1, arctic[dest].read('some_a_ts1').data)
    assert_frame_equal(ts1, arctic[dest].read('some_b_ts1').data)
    assert logger.info.call_args_list == [call('Copying data from %s -> %s' % (src_host, dest_host)),
                                          call('Copying: 3 symbols')]
    assert arctic[dest].read_audit_log('some_a_ts1')[0]['message'] == 'CR101'


def test_copy_data_doesnt_exist(arctic, mongo_host):
    src = 'user.library'
    dest = 'user.library2'

    # Create the user against the current mongo database
    src_host = src + '@' + mongo_host
    dest_host = dest + '@' + mongo_host
    with patch('arctic.scripts.arctic_copy_data.logger') as logger:
        run_as_main(mcd.main, '--src', src_host, '--dest', dest_host, '--log', 'CR101', 'some_ts')

    assert logger.info.call_args_list == [call('Copying data from %s -> %s' % (src_host, dest_host)),
                                          call('Copying: 0 symbols')]
    assert logger.warn.call_args_list == [call('No symbols found that matched those provided.')]

@pytest.mark.parametrize('source_ts', [read_str_as_pandas("""             times | near"""), None])
def test_copy_empty_data(arctic, mongo_host, source_ts):
    src = 'user.library'
    dest = 'user.library2'
    # Put ts, ts1 in library
    arctic[src].write('some_ts', source_ts)

    # Put some other value for ts in library2
    arctic[dest].write('some_ts', ts)

    # Create the user against the current mongo database
    src_host = src + '@' + mongo_host
    dest_host = dest + '@' + mongo_host
    with patch('arctic.scripts.arctic_copy_data.logger') as logger:
        run_as_main(mcd.main, '--src', src_host, '--dest', dest_host, '--log', 'CR101', '--splice', 'some_ts')

    assert_frame_equal(ts, arctic[dest].read('some_ts').data)
    assert logger.info.call_args_list == [call('Copying data from %s -> %s' % (src_host, dest_host)),
                                          call('Copying: 1 symbols')]
    assert logger.warn.call_args_list == [call('Symbol: some_ts already exists in destination, splicing in new data')]

    # As the destination data is unchanged, no writing takes place and the audit log is empty.
    assert len(arctic[dest].read_audit_log('some_ts')) == 0
