from twitter.thermos.config.schema import *
from gen.twitter.mesos.constants import DEFAULT_ENVIRONMENT


class MesosContext(Struct):
  # The role running the job
  role        = Required(String)

  # The cluster in which the job is running
  cluster     = Required(String)

  # The instance id (i.e. replica id, shard id) in the context of a task
  instance    = Required(Integer)

  # The filename of the package associated with this job
  # DEPRECATED in favor of using {{packer[role][package][version].package}}
  package     = String

  # The URI of the package associated with this job
  # DEPRECATED in favor of using {{packer[role][package][version].package_uri}}
  package_uri = String


# AppApp layout setup
class AppPackage(Struct):
  name    = Required(String)
  version = Default(String, 'latest')

class AppLayout(Struct):
  packages = Default(List(AppPackage), [])


# The object bound into the {{packer}} namespace.
# Referenced by
#  {{packer[role][name][version]}}
#
# Where version =
#    number (integer)
#    'live' (live package)
#    'latest' (highest version number)
#
# For example if you'd like to create a copy process for a particular
# package,
#   copy_latest = Process(
#     name = 'copy-{{package_name}}',
#     cmdline = '{{packer[{{role}}][{{package_name}}][latest].copy_command}}')
#   processes = [
#     copy_latest.bind(package_name = 'labrat'),
#     copy_latest.bind(package_name = 'packer')
#   ]
class PackerObject(Struct):
  package = String
  package_uri = String

  # 'copy_command' is bound to the command in the context
  copy_command = String

  tunnel_host = Default(String, 'nest2.corp.twitter.com')
  local_copy_command = Default(String,
      'ssh {{tunnel_host}} hadoop fs -cat {{package_uri}} > {{package}}')
  remote_copy_command = Default(String,
      'hadoop fs -copyToLocal {{package_uri}} {{package}}')


# Packer package information
@Provided(mesos=MesosContext)
class PackerPackage(Struct):
  name = Required(String)
  role = Default(String, '{{mesos.role}}')
  version = Required(String)

Package = PackerPackage


class UpdateConfig(Struct):
  batch_size                  = Default(Integer, 1)
  restart_threshold           = Default(Integer, 60)
  watch_secs                  = Default(Integer, 30)
  max_per_shard_failures      = Default(Integer, 0)
  max_total_failures          = Default(Integer, 0)


class HealthCheckConfig(Struct):
  initial_interval_secs    = Default(Float, 60.0)
  interval_secs            = Default(Float, 30.0)
  timeout_secs             = Default(Float, 1.0)
  max_consecutive_failures = Default(Integer, 0)


class Announcer(Struct):
  primary_port = Default(String, 'http')

  # Portmap can either alias two ports together, e.g.
  #   aurora <= http
  # Or it can be used to alias static ports to endpoints, e.g.
  #   http <= 80
  #   https <= 443
  #   aurora <= https
  portmap      = Default(Map(String, String), {
    'aurora': '{{primary_port}}'
  })


# The thermosConfig populated inside of TwitterTaskInfo.
class MesosTaskInstance(Struct):
  task                       = Required(Task)
  layout                     = AppLayout
  instance                   = Required(Integer)
  role                       = Required(String)
  announce                   = Announcer
  environment                = Default(String, DEFAULT_ENVIRONMENT)
  health_check_interval_secs = Default(Integer, 30) # DEPRECATED (MESOS-2649)
  health_check_config        = Default(HealthCheckConfig, HealthCheckConfig())


class MesosJob(Struct):
  name          = Default(String, '{{task.name}}')
  role          = Required(String)
  contact       = String
  cluster       = Required(String)
  environment   = Default(String, DEFAULT_ENVIRONMENT)
  instances     = Default(Integer, 1)
  task          = Required(Task)
  recipes       = List(String)
  announce      = Announcer

  cron_schedule = String
  cron_policy   = String          # these two are aliases of each other.  default is KILL_EXISTING
  cron_collision_policy = String  # if unspecified.
                                  # cron_policy is DEPRECATED (MESOS-2491) in favor of
                                  # cron_collision_policy.

  update_config = Default(UpdateConfig, UpdateConfig())

  constraints                = Map(String, String)
  daemon                     = Integer              # daemon and service are booleans that are
  service                    = Integer              # aliased together.  daemon is DEPRECATED
                                                    # (MESOS-2492) # in favor of service.  by
                                                    # default, service is False.
  max_task_failures          = Default(Integer, 1)
  production                 = Default(Integer, 0)  # boolean
  priority                   = Default(Integer, 0)
  health_check_interval_secs = Integer # DEPRECATED in favor of health_check_config (MESOS-2649).
  health_check_config        = HealthCheckConfig
  task_links                 = Map(String, String)

  layout        = AppLayout      # DEPRECATED in favor of directory sandboxes
  package       = PackerPackage  # DEPRECATED in favor of {{packer}} namespaces.


Job = MesosJob
Service = Job(service = True)