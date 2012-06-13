Core Concepts
============

Environment Template
--------------------

A list of Instances, detailing the Services that will run on them, and
any parameters required by the Instance Provisioner to create/manage the
instance in question.

Service Definition
------------------

Details the location of artifacts, Configuration manifest (Puppet in
this case), DNS templates etc. Used during instance configuration to
install the required services, and ensure they are running.

instance Provisioning
-----------------

The act of providing an instance to be configured. Initially, we'll be
using an AWS-based instance Provider, but we could support Vagrant,
libvrt, Rackspace etc.

instance Providers are responsible for instance lifecycle operations, as well
as providing metadata about a instance.

instance Configuration
------------------

The act of placing a instance into a given state, using Puppet for most of
the heavy lifting.
