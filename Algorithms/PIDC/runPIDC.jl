# Include packages
import Pkg
Pkg.activate("/storage/ideas/is-schockalingam6-0/dev/NetworkInference.jl")
using NetworkInference
using LightGraphs

algorithm = PIDCNetworkInference()

dataset_name = string(ARGS[1])

@time genes = get_nodes(dataset_name);

@time network = InferredNetwork(algorithm, genes);

write_network_file(string(ARGS[2]), network);

