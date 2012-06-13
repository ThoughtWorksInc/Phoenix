Goals
=====

The goal of this tech lab project is:

* Clearly explain the core concepts involved in infrastructure
automaton of Environments. We don't have the patterns, the shared
language, to talk about this stuff. I want to make a stab at doing
that.

* Implement a set of scripts that use those concepts.

For the framework/system itself, we have 4 milestones we have
sketched out. We have a fixed period of time, so will do what we can,
but currently these are:

 1. Model the concept of environment, service, & instance. Support
provisioning of instances on AWS, configuration of instances using Puppet
 
 2. Show we can ue an alternative provisioner, in the form of LXC (ideal) or Vagrant (fallback if LXC/libvrt is too complex), to
ensure we are modelling at the right level & haven't missed some
concepts

 3. Support service isolation/load balancing. Again, to ensure we
haven't missed some concept of 'service' or the like.
 
 4. Setup log aggregation, dashboarding & trending tools for the
above, to make a kick-ass demo
 
 5. Windows support
