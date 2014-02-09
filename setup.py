#!/usr/bin/env python

from distutils.core import setup

a=setup(name="pbsclusterviz",
      version="0.7a",
      description="PBS Cluster Visualisation",
      author="Paul Cochrane",
      author_email="paul@liekut.de",
      maintainer="Paul Cochrane",
      maintainer_email="paul@liekut.de",
      url="http://pbsclusterviz.sourceforge.net",
      license="GPL",
      keywords="PBS Torque Maui Cluster HPC Visualisation",
      platforms="OS Independent",
      packages=['pbsclusterviz'],
      scripts=[
                'bin/cluster_status',
                'bin/gen_nodes_file',
                ],
      data_files=[('/etc/pbsclusterviz.d',
                    [
                    'etc/pbsclusterviz.d/nodes',
                    'etc/pbsclusterviz.d/clusterviz.conf'
                    ])],
)

# vim: expandtab shiftwidth=4:
