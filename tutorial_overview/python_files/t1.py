import dolfinx
import dolfinx.cpp
import dolfinx.mesh
import dolfinx.plotting
import matplotlib.pyplot
import numpy
import ufl
from mpi4py import MPI
from petsc4py import PETSc

# Create the mesh and define function space
mesh = dolfinx.UnitSquareMesh(MPI.COMM_WORLD, 8, 8, dolfinx.cpp.mesh.CellType.triangle)
V = dolfinx.FunctionSpace(mesh, ("CG", 1))

# Define boundary condition
uD = dolfinx.Function(V)
uD.interpolate(lambda x: 1 + x[0]**2 + 2 * x[1]**2)
uD.vector.ghostUpdate(addv=PETSc.InsertMode.INSERT, mode=PETSc.ScatterMode.FORWARD)
fdim = mesh.topology.dim - 1
boundary_facets = dolfinx.mesh.locate_entities_boundary(mesh, fdim,
                                                        lambda x: numpy.full(x.shape[1], True, dtype=numpy.bool))
bc = dolfinx.DirichletBC(uD, dolfinx.fem.locate_dofs_topological(V, fdim, boundary_facets))

# Define variational problem
u = ufl.TrialFunction(V)
v = ufl.TestFunction(V)
f = dolfinx.Constant(mesh, -6)
a = ufl.dot(ufl.grad(u), ufl.grad(v)) * ufl.dx
L = f * v * ufl.dx

# Compute solution
uh = dolfinx.Function(V)
dolfinx.solve(a == L, uh, bc, petsc_options={"ksp_type": "preonly", "pc_type": "lu"})
uh.vector.ghostUpdate(addv=PETSc.InsertMode.INSERT, mode=PETSc.ScatterMode.FORWARD)

# Plot solution
dolfinx.plotting.plot(uh)
dolfinx.plotting.plot(mesh, color="k")
matplotlib.pyplot.savefig("uh.png")

# Compute exact solution
V2 = dolfinx.FunctionSpace(mesh, ("CG", 2))
uex = dolfinx.Function(V2)
uex.interpolate(lambda x: 1 + x[0]**2 + 2 * x[1]**2)
uex.vector.ghostUpdate(addv=PETSc.InsertMode.INSERT, mode=PETSc.ScatterMode.FORWARD)

# Compute error in L2 norm
error_L2 = numpy.sqrt(dolfinx.fem.assemble_scalar(ufl.inner(uh - uex, uh - uex) * ufl.dx))

# Compute maximum error at the vertices
u_vertex_values = uh.compute_point_values()
u_ex_vertex_values = uex.compute_point_values()
error_max = numpy.max(numpy.abs(u_vertex_values - u_ex_vertex_values))

# Print errors
print("Error_L2 = {0:.2e}".format(error_L2))
print("Error_max = {0:.2e}".format(error_max))
