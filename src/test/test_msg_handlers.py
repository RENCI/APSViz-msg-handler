# SPDX-FileCopyrightText: 2022 Renaissance Computing Institute. All rights reserved.
# SPDX-FileCopyrightText: 2023 Renaissance Computing Institute. All rights reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-License-Identifier: LicenseRef-RENCI
# SPDX-License-Identifier: MIT

"""
    Test ecflow message handler - Tests the handling of an ecflow message

    Authors: Lisa Stillwell, Phil Owen @RENCI.org
"""
import os
import json

from src.common.queue_utils import QueueUtils
from src.common.pg_impl import PGImplementation
from src.common.queue_callbacks import QueueCallbacks

# these are the currently expected ecflow params that were transformed into ASGS legacy params
ecflow_expected_transformed_params: dict = {'physical_location': 'RENCI', 'monitoring.rmqmessaging.locationname': 'RENCI', 'instance_name': 'ec95d',
                                            'instancename': 'ec95d', 'uid': '90161888', 'ADCIRCgrid': 'ec95d', 'adcirc.gridname': 'ec95d',
                                            'currentdate': '230206', 'currentcycle': '12', 'advisory': '2023030112', 'asgs.enstorm': 'gfsforecast',
                                            'enstorm': 'gfsforecast', 'stormname': 'none', 'forcing.tropicalcyclone.stormname': 'none',
                                            'config.coupling.waves': '0', 'forcing.tropicalcyclone.vortexmodel': 'NA',
                                            'downloadurl':
                                                'https://localhost/thredds/fileServer/2023/gfs/2023020612/ec95d/ht-ncfs.renci.org/ec95d/gfsforecast'}

# these are the currently expected hecras params that were transformed into ASGS legacy params
hecras_expected_transformed_params: dict = {'ADCIRCgrid': 'ec95d', 'adcirc.gridname': 'ec95d', 'advisory': '2023030112',
                                            'asgs.enstorm': 'gfsforecast', 'config.coupling.waves': '0', 'currentcycle': '06',
                                            'currentdate': '230206', 'downloadurl': 'http://hecrastest.com/max_wse.tif', 'enstorm': 'gfsforecast',
                                            'forcing.advisory': '2023030112', 'forcing.ensemblename': 'gfsforecast', 'forcing.metclass': 'synoptic',
                                            'forcing.stormname': None, 'forcing.tropicalcyclone.stormname': None,
                                            'forcing.tropicalcyclone.vortexmodel': 'NA', 'forcing.vortexmodel': 'NA', 'forcing.waves': '0',
                                            'instance_name': 'ec95d', 'instancename': 'ec95d', 'monitoring.rmqmessaging.locationname': 'RENCI',
                                            'output.downloadurl': 'http://hecrastest.com/max_wse.tif', 'physical_location': 'RENCI',
                                            'stormname': None, 'suite.adcirc.gridname': 'ec95d', 'suite.instance_name': 'ec95d',
                                            'suite.physical_location': 'RENCI', 'suite.project_code': 'hecras_test_renci', 'suite.uid': '94836645',
                                            'time.currentcycle': '06', 'time.currentdate': '230206', 'uid': '94836645'}


def test_insert_asgs_status_msg():
    """
    Tests the parsing of asgs data and insertion into the DB

    :return:
    """
    # specify the DB to get a connection
    # note the extra comma makes this single item a singleton tuple
    db_name: tuple = ('asgs',)

    # define and init the object that will handle ASGS DB operations
    db_info = PGImplementation(db_name)

    # load the json
    with open('test_asgs_status_msg.json', encoding='UTF-8') as test_fh:
        status_items = json.loads(test_fh.read())

    # get the state type id. lets just set this to running for this test run
    state_id = db_info.get_lu_id('RUNN', "state_type", context='test_insert_asgs_status_msg()')

    # get the site id
    site_id = db_info.get_lu_id(status_items.get('physical_location'), 'site', context='test_insert_asgs_status_msg()')

    # insert an instance record into the DB to get things primed
    instance_id = db_info.insert_instance(state_id, site_id, status_items, context='test_insert_asgs_status_msg()')

    # test the result, empty str == success
    assert instance_id >= 0


def test_insert_asgs_config_items():
    """
    Tests the parsing of hec/ras data and insertion into the DB

    :return:
    """
    # specify the DB to get a connection
    # note the extra comma makes this single item a singleton tuple
    db_name: tuple = ('asgs',)

    # define and init the object that will handle ASGS DB operations
    db_info = PGImplementation(db_name)

    # load the json
    with open('test_asgs_run_props.json', encoding='UTF-8') as test_fh:
        run_props = json.loads(test_fh.read())

    # get the param array into a dict
    param_list: dict = {'physical_location': run_props['physical_location'], 'uid': run_props['uid'], 'instance_name': run_props['instance_name'],
                        'workflow_type': 'ASGS', 'supervisor_job_status': 'debug', 'product_type': 'asgs'}

    # convert the asgs object into a single dict (like ecflow and hecras)
    param_list.update({x[0]: x[1] for x in run_props['param_list']})

    # get the state type id. lets just set this to running for this test run
    state_id = db_info.get_lu_id('RUNN', "state_type", context='test_insert_asgs_config_items()')

    # get the site id
    site_id = db_info.get_lu_id(param_list.get('physical_location'), 'site', context='test_insert_asgs_config_items()')

    # insert an instance record into the DB to get things primed
    instance_id = db_info.insert_instance(state_id, site_id, param_list, context='test_insert_asgs_config_items()')

    # insert the run params into the DB
    ret_val = db_info.insert_config_items(instance_id, param_list)

    # test the result, empty str == success
    assert ret_val is None


def test_insert_ecflow_config_items():
    """
    Tests the parsing of ecflow data and insertion into the DB

    :return:
    """
    # specify the DB to get a connection
    # note the extra comma makes this single item a singleton tuple
    db_name: tuple = ('asgs',)

    # define and init the object that will handle ASGS DB operations
    db_info = PGImplementation(db_name)

    # instantiate the utility class
    queue_utils = QueueUtils(_queue_name='')

    # load the json
    with open('test_ecflow_run_props.json', encoding='UTF-8') as test_fh:
        run_props = json.loads(test_fh.read())

    # transform the ecflow params into addition al asgs params
    ret_val = queue_utils.extend_msg_to_asgs_legacy(run_props)

    # add in the expected transformations
    run_props.update(ecflow_expected_transformed_params)

    # check the result
    assert ret_val == run_props

    # get the state type id. lets just set this to running for this test run
    state_id = db_info.get_lu_id('RUNN', "state_type", context='test_insert_ecflow_config_items()')

    # get the site id
    site_id = db_info.get_lu_id(run_props.get('suite.physical_location'), 'site', context='test_insert_ecflow_config_items()')

    # insert an instance record into the DB to get things primed
    instance_id = db_info.insert_instance(state_id, site_id, run_props, context='test_insert_ecflow_config_items()')

    # make sure we are in debug mode and have a workflow type
    run_props.update({'workflow_type': 'ECFLOW', 'supervisor_job_status': 'debug'})

    # insert the run params into the DB
    ret_val = db_info.insert_config_items(instance_id, run_props)

    # test the result, empty str == success
    assert ret_val is None


def test_insert_hecras_config_items():
    """
    Tests the parsing of hec/ras data and insertion into the DB

    :return:
    """
    # specify the DB to get a connection
    # note the extra comma makes this single item a singleton tuple
    db_name: tuple = ('asgs',)

    # define and init the object that will handle ASGS DB operations
    db_info = PGImplementation(db_name)

    # instantiate the utility class
    queue_utils = QueueUtils(_queue_name='')

    # load the json
    with open('test_hecras_run_props.json', encoding='UTF-8') as test_fh:
        run_props = json.loads(test_fh.read())

    # transform the ecflow params into addition al asgs params
    ret_val = queue_utils.extend_msg_to_asgs_legacy(run_props)

    # add in the expected transformations
    run_props.update(hecras_expected_transformed_params)

    # check the result
    assert ret_val == run_props

    # get the state type id. lets just set this to running for this test run
    state_id = db_info.get_lu_id('RUNN', "state_type", context='test_insert_hecras_config_items()')

    # get the site id
    site_id = db_info.get_lu_id(run_props.get('suite.physical_location'), 'site', context='test_insert_hecras_config_items()')

    # insert an instance record into the DB to get things primed
    instance_id = db_info.insert_instance(state_id, site_id, run_props, context='test_insert_hecras_config_items()')

    # make sure we are in debug mode and have a workflow type
    run_props.update({'workflow_type': 'HECRAS', 'supervisor_job_status': 'debug'})

    # insert the run params into the DB
    ret_val = db_info.insert_config_items(instance_id, run_props)

    # test the result, empty str == success
    assert ret_val is None


def test_ecflow_run_time_queue_callback():
    """
    Tests the handling of an ecflow run time msg

    :return:
    """
    # load the json
    with open('test_ecflow_uga_rt_msg.json', encoding='UTF-8') as test_fh:
        msg = test_fh.readline()

    # instantiate the utility class
    queue_callback = QueueCallbacks(_queue_name='')

    # call the msg handler callback
    success = queue_callback.ecflow_run_time_status_callback(None, None, None, msg)

    # check for pass/fail
    assert success is True


def test_ecflow_run_props_queue_callback():
    """
    Tests the handling of an ecflow run time msg

    :return:
    """
    # load the json
    with open('test_new_run_props_msg.json', encoding='UTF-8') as test_fh:
        msg = test_fh.readline()

    # instantiate the utility class
    queue_callback = QueueCallbacks(_queue_name='')

    # call the msg handler callback
    success = queue_callback.ecflow_run_props_callback(None, None, None, msg)

    # check for pass/fail
    assert success is True


def test_hecras_queue_callback():
    """
    Tests the handling of a hec/ras run time msg

    :return:
    """
    # load the json
    with open('test_hecras_run_props.json', encoding='UTF-8') as test_fh:
        msg = test_fh.readline()

    # instantiate the utility class
    queue_callback = QueueCallbacks(_queue_name='')

    # call the msg handler callback
    success = queue_callback.hecras_run_props_callback(None, None, None, msg)

    # check for pass/fail
    assert success is True
