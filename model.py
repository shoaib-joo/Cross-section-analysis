"""Centerline model of a thin-walled cross-section.

Notation and sign conventions follow Kindmann & Kraus,
"Steel Structures: Design using FEM":

* ``y1``/``z1``  - arbitrary input coordinate system
* ``_1`` suffix  - quantity referred to the arbitrary input system
* ``_2`` suffix  - quantity referred to axes through the centre of gravity,
                   parallel to the input axes
* ``y``/``z``    - principal axes through the centre of gravity
"""

import math

# Second moments smaller than this fraction of (Ayy + Azz) are treated as zero.
_REL_TOL = 1e-12


class Node:
    """Represents a point in 2D space with y and z coordinates."""
    def __init__(self,y1:float,z1:float,node_id: int):
        """Initialize a Node with coordinates and an identifier.
        
        Args:
            y1: Y-coordinate of the node (initial arbitrary coordinate system)
            z1: Z-coordinate of the node (initial arbitrary coordinate system)
            node_id: Unique identifier for the node.
        """
        self.y1 = y1
        self.z1 = z1
        self.id = node_id
        
    def __repr__(self):
        """Return a string representation of the Node."""
        return f"Node({self.id}: y={self.y1}, z={self.z1})"
    
class Element:
    """Represents a structural element connecting two nodes with a given thickness."""
    def __init__(self, element_id: int, start_node: Node , end_node : Node, thickness: float):
        """Initialize an Element.
        
        Args:
            element_id: Unique identifier for the element.
            start_node: Starting Node of the element.
            end_node: Ending Node of the element.
            thickness: Thickness of the element.
        """
        self.element_id = element_id
        self.start_node = start_node
        self.end_node = end_node
        self.thickness = thickness
        
    @property
    def length(self):
        """Calculate the length of the element."""
        dy = self.end_node.y1 - self.start_node.y1
        dz = self.end_node.z1 - self.start_node.z1
        return math.sqrt(dy**2 + dz**2)
    
    @property
    def area(self):
        """Calculate the cross-sectional area of the element."""
        return self.thickness * self.length
    
    @property
    def first_moment_y1i(self):
        """Calculate the first moment of area about the Y-axis."""
        return 0.5 * self.area * (self.start_node.y1 + self.end_node.y1)
        
    @property
    def first_moment_z1i(self):
        """Calculate the first moment of area about the Z-axis."""
        return 0.5 * self.area * (self.start_node.z1 + self.end_node.z1)
    
    @property
    def Ayy_1i(self):
        """Calculate Ayy1i"""
        return (self.start_node.y1**2 + self.start_node.y1*self.end_node.y1 + self.end_node.y1**2)*self.area/3
    
    
    @property
    def Azz_1i(self):
        """Calculate Azz1i"""
        return (self.start_node.z1**2 + self.start_node.z1*self.end_node.z1 + self.end_node.z1**2)*self.area/3
    
    @property
    def Ayz_1i(self):
        """Calculate Ayz1i"""
        return (2*self.start_node.y1*self.start_node.z1 + 2*self.end_node.y1*self.end_node.z1 + self.end_node.z1*self.start_node.y1 + self.start_node.z1*self.end_node.y1 )*self.area/6
    
    
    
    
    
class CrossSection:
    """Represents a cross-section composed of multiple nodes and elements."""
    def __init__(self,thickness=None):
        """Initialize a CrossSection.
        
        Args:
            thickness: Default thickness for elements added without their own.
        """
        self.thickness = thickness
        self.nodes: dict[int, Node] = {}
        self.elements: list[Element] = []
        
    def add_node(self,node_id,y,z):
        """Add a node to the cross-section.
        
        Args:
            node_id: Unique identifier for the node.
            y: Y-coordinate.
            z: Z-coordinate.
        """
        self.nodes[node_id] = Node(y,z,node_id)
            
    def add_elements(self, id ,start_node:Node, end_node:Node):
        """Add an element connecting two nodes to the cross-section.
        
        Args:
            id: Unique identifier for the element.
            start_node: Starting Node of the element.
            end_node: Ending Node of the element.
        """
        start = self.nodes[start_node.id]
        end = self.nodes[end_node.id]
        element = Element(id,start,end,self.thickness)
        self.elements.append(element)

    def add_element(self, start_id: int, end_id: int, element_id: int | None = None,
                    thickness: float | None = None) -> Element:
        """Add an element between two existing nodes, referenced by node id.

        Args:
            start_id: Id of the start node.
            end_id: Id of the end node.
            element_id: Optional element id. Defaults to the next free number.
            thickness: Thickness of this plate. Defaults to the section's thickness.

        Returns:
            The newly created Element.
        """
        if element_id is None:
            element_id = len(self.elements) + 1
        if thickness is None:
            thickness = self.thickness
        if thickness is None:
            raise ValueError("No thickness given for the element and the section has no default.")
        element = Element(element_id, self.nodes[start_id], self.nodes[end_id], thickness)
        self.elements.append(element)
        return element

    @classmethod
    def from_geometry(cls, coordinates, connections, thickness) -> "CrossSection":
        """Build a cross-section from node coordinates and element connections.

        Args:
            coordinates: Sequence of (y1, z1) pairs. Nodes are numbered from 1
                in the order given.
            connections: Sequence of (start_node_id, end_node_id) pairs.
            thickness: One wall thickness for all plates, or a sequence with
                one thickness per connection.
        """
        connections = list(connections)
        if isinstance(thickness, (int, float)):
            thicknesses = [float(thickness)] * len(connections)
        else:
            thicknesses = [float(t) for t in thickness]
            if len(thicknesses) != len(connections):
                raise ValueError(f"Got {len(thicknesses)} thicknesses for {len(connections)} plates.")

        uniform = len(set(thicknesses)) == 1
        cross_section = cls(thicknesses[0] if uniform else None)
        for node_id, (y1, z1) in enumerate(coordinates, start=1):
            cross_section.add_node(node_id, y1, z1)
        for (start_id, end_id), t in zip(connections, thicknesses):
            cross_section.add_element(start_id, end_id, thickness=t)
        return cross_section

    @property     
    def total_area(self):
        """Calculate the total cross-sectional area."""
        return sum(e.area for e in self.elements)

    @property
    def first_moment_y_1(self):
        """Calculate the total first moment of area about the Y-axis."""
        return sum(e.first_moment_y1i for e in self.elements)
    
    @property
    def first_moment_z_1(self):
        """Calculate the total first moment of area about the Z-axis."""
        return sum(e.first_moment_z1i for e in self.elements)
        
    @property
    def Y1s(self) -> float:
        """COG location in Y direction."""
        if self.total_area == 0:
            return 0.0
        return self.first_moment_y_1 / self.total_area

    @property
    def Z1s(self) -> float:
        """COG location in Z direction."""
        if self.total_area == 0:
            return 0.0
        return self.first_moment_z_1 / self.total_area
    
    @property
    def A_yy_1(self) -> float:
        """Second moment of area  A_yy = integral(y1^2 dA)  in the input system."""
        if self.total_area == 0:
            return 0.0
        return sum(e.Ayy_1i for e in self.elements)

    @property
    def A_zz_1(self) -> float:
        """Second moment of area  A_zz = integral(z1^2 dA)  in the input system."""
        if self.total_area == 0:
            return 0.0
        return sum(e.Azz_1i for e in self.elements)

    @property
    def A_yz_1(self) -> float:
        """Product moment of area  A_yz = integral(y1*z1 dA)  in the input system."""
        if self.total_area == 0:
            return 0.0
        return sum(e.Ayz_1i for e in self.elements)


    #TRANSFORMATION OF COORDINATE SYSTEM CENTRE TO COG

    @property
    def Ayz_2(self) -> float:
        """Product moment A_yz about the COG, axes parallel to the input axes."""
        if self.total_area == 0:
            return 0.0
        return self.A_yz_1 - self.Y1s*self.Z1s*self.total_area

    @property
    def Ayy_2(self) -> float:
        """Second moment A_yy about the COG, axes parallel to the input axes."""
        if self.total_area == 0:
            return 0.0
        return self.A_yy_1 - (self.Y1s**2)*self.total_area

    @property
    def Azz_2(self) -> float:
        """Second moment A_zz about the COG, axes parallel to the input axes."""
        if self.total_area == 0:
            return 0.0
        return self.A_zz_1 - (self.Z1s**2)*self.total_area

    #CALCULATING ALPHA

    @property
    def alpha(self) -> float:
        """Rotation angle of the principal axes in degrees.

        tan(2*alpha) = 2*A_yz / (A_yy - A_zz)

        The result lies in [-45, 45] degrees, i.e. the principal axes are the
        ones closest to the input axes, so a section that is already aligned
        (A_yz = 0) is never rotated.
        """
        Ayy, Azz, Ayz = self.Ayy_2, self.Azz_2, self.Ayz_2
        tol = _REL_TOL * (abs(Ayy) + abs(Azz))
        if abs(Ayz) <= tol:
            return 0.0
        if abs(Ayy - Azz) <= tol:
            return math.copysign(45.0, Ayz)
        return math.degrees(math.atan(2*Ayz / (Ayy - Azz))) / 2

    #CALCULATING MOMENTS OF INERTIA

    @property
    def I_y(self) -> float:
        """Principal moment of inertia about the y axis:  I_y = integral(z^2 dA)."""
        a = math.radians(self.alpha)
        s, c = math.sin(a), math.cos(a)
        return self.Azz_2*c**2 + self.Ayy_2*s**2 - 2*self.Ayz_2*s*c

    @property
    def I_z(self) -> float:
        """Principal moment of inertia about the z axis:  I_z = integral(y^2 dA)."""
        a = math.radians(self.alpha)
        s, c = math.sin(a), math.cos(a)
        return self.Ayy_2*c**2 + self.Azz_2*s**2 + 2*self.Ayz_2*s*c

    #TRANSFORMATION FROM ARBITRARY SELECTED COS TO COG CENTERED COORDINATE SYSTEM
    
    def y(self, y_coordinate, z_coordinate) -> float:
        """Transform y coordinate to COG-centered coordinate system."""
        return (y_coordinate - self.Y1s)*math.cos(math.radians(self.alpha)) + (z_coordinate - self.Z1s)*math.sin(math.radians(self.alpha))
    
    def z(self, y_coordinate, z_coordinate) -> float:
        """Transform z coordinate to COG-centered coordinate system."""
        return (z_coordinate - self.Z1s)*math.cos(math.radians(self.alpha)) - (y_coordinate - self.Y1s)*math.sin(math.radians(self.alpha))

    # ------------------------------------------------------------------
    # DERIVED VALUES
    # ------------------------------------------------------------------

    def _principal_nodes(self) -> dict:
        """Node id -> (y, z) in the principal system."""
        a = math.radians(self.alpha)
        s, c = math.sin(a), math.cos(a)
        y0, z0 = self.Y1s, self.Z1s
        return {nid: ((n.y1 - y0)*c + (n.z1 - z0)*s, (n.z1 - z0)*c - (n.y1 - y0)*s)
                for nid, n in self.nodes.items()}

    def _used_principal_nodes(self) -> dict:
        used = {nid for e in self.elements for nid in (e.start_node.id, e.end_node.id)}
        return {nid: yz for nid, yz in self._principal_nodes().items() if nid in used}

    @property
    def i_y(self) -> float:
        """Radius of gyration about the y axis:  i_y = sqrt(I_y / A)."""
        return math.sqrt(max(self.I_y, 0.0) / self.total_area) if self.total_area else 0.0

    @property
    def i_z(self) -> float:
        """Radius of gyration about the z axis:  i_z = sqrt(I_z / A)."""
        return math.sqrt(max(self.I_z, 0.0) / self.total_area) if self.total_area else 0.0

    @property
    def W_y(self) -> float:
        """Elastic section modulus  W_y = I_y / max|z|  (extreme fibre on the centerline)."""
        z_max = max((abs(z) for _, z in self._used_principal_nodes().values()), default=0.0)
        return self.I_y / z_max if z_max > 0 else 0.0

    @property
    def W_z(self) -> float:
        """Elastic section modulus  W_z = I_z / max|y|  (extreme fibre on the centerline)."""
        y_max = max((abs(y) for y, _ in self._used_principal_nodes().values()), default=0.0)
        return self.I_z / y_max if y_max > 0 else 0.0

    def _plastic_modulus(self, component: int) -> float:
        P = self._principal_nodes()
        plates = [(P[e.start_node.id][component], P[e.end_node.id][component], e.area)
                  for e in self.elements]
        return _plastic_modulus(plates)

    @property
    def W_pl_y(self) -> float:
        """Plastic section modulus for bending about an axis parallel to y.

        The axis is the one that halves the area, which is where the plastic
        neutral axis lies. It differs from the y axis for unsymmetric sections.
        """
        return self._plastic_modulus(1)

    @property
    def W_pl_z(self) -> float:
        """Plastic section modulus for bending about an axis parallel to z."""
        return self._plastic_modulus(0)

    # ------------------------------------------------------------------
    # TOPOLOGY: spanning tree and closed cells
    # ------------------------------------------------------------------

    def _topology(self) -> dict:
        """Describe how the plates are connected.

        A spanning tree is laid over the section. Every plate that is not part
        of the tree closes exactly one loop ("cell"), so open sections have no
        such plates and a box has one.

        Returns a dict with
            adj     node id -> list of elements
            root    root node of the tree (the most central node)
            parent  node id -> (parent node id, connecting element), None for the root
            order   node ids, root first, every node after its parent
            cuts    elements that are not in the tree
            cycles  one entry per cut element:
                      'sigma' element id -> +1/-1, loop direction relative to the element
                      'steps' the loop as a list of (from node id, to node id)
        """
        if not self.elements:
            raise ValueError("The cross-section has no elements.")
        ids = [e.element_id for e in self.elements]
        if len(set(ids)) != len(ids):
            raise ValueError("Element ids must be unique.")

        adj: dict = {}
        for e in self.elements:
            if e.length <= 0:
                raise ValueError(f"Element {e.element_id} has zero length.")
            if e.thickness <= 0:
                raise ValueError(f"Element {e.element_id} has no thickness.")
            adj.setdefault(e.start_node.id, []).append(e)
            adj.setdefault(e.end_node.id, []).append(e)

        def other_end(e, nid):
            return e.end_node.id if e.start_node.id == nid else e.start_node.id

        def bfs(root):
            parent, depth, order = {root: None}, {root: 0}, [root]
            i = 0
            while i < len(order):
                cur = order[i]
                i += 1
                for e in adj[cur]:
                    nxt = other_end(e, cur)
                    if nxt not in parent:
                        parent[nxt] = (cur, e)
                        depth[nxt] = depth[cur] + 1
                        order.append(nxt)
            return parent, depth, order

        # Root = most central node, so that open sections are traversed from
        # their free ends inwards.
        best = None
        for candidate in sorted(adj):
            parent, depth, order = bfs(candidate)
            if len(order) != len(adj):
                raise ValueError("All plates of the cross-section must be connected.")
            eccentricity = max(depth.values())
            if best is None or eccentricity < best[0]:
                best = (eccentricity, candidate, parent, order)
        _, root, parent, order = best

        tree_ids = {link[1].element_id for link in parent.values() if link is not None}
        cuts = [e for e in self.elements if e.element_id not in tree_ids]

        def path_to_root(nid):
            path = [nid]
            while parent[nid] is not None:
                nid = parent[nid][0]
                path.append(nid)
            return path

        cycles = []
        for cut in cuts:
            a, b = cut.start_node.id, cut.end_node.id
            up, down = path_to_root(b), path_to_root(a)
            in_down = set(down)
            meet = next(n for n in up if n in in_down)
            up = up[:up.index(meet) + 1]                 # b ... meeting node
            down = down[:down.index(meet) + 1][::-1]     # meeting node ... a

            sigma = {cut.element_id: 1.0}
            steps = [(a, b)]
            for u, v in zip(up, up[1:]):                 # towards the root
                e = parent[u][1]
                sigma[e.element_id] = 1.0 if e.start_node.id == u else -1.0
                steps.append((u, v))
            for u, v in zip(down, down[1:]):             # away from the root
                e = parent[v][1]
                sigma[e.element_id] = 1.0 if e.start_node.id == u else -1.0
                steps.append((u, v))
            cycles.append({"sigma": sigma, "steps": steps})

        return {"adj": adj, "root": root, "parent": parent, "order": order,
                "cuts": cuts, "cycles": cycles}

    def _cell_matrix(self, topo: dict) -> list:
        """F_ij = sum over shared plates of  l / t  (with the loop directions)."""
        elems = {e.element_id: e for e in self.elements}
        cycles = topo["cycles"]
        F = [[0.0] * len(cycles) for _ in cycles]
        for i, ci in enumerate(cycles):
            for j, cj in enumerate(cycles):
                for eid, si in ci["sigma"].items():
                    sj = cj["sigma"].get(eid)
                    if sj:
                        F[i][j] += si * sj * elems[eid].length / elems[eid].thickness
        return F

    @property
    def n_cells(self) -> int:
        """Number of closed cells (0 for an open section)."""
        return len(self._topology()["cycles"])

    # ------------------------------------------------------------------
    # TORSION AND WARPING
    # ------------------------------------------------------------------

    def _torsion(self) -> dict:
        """Torsion constant, warping ordinate, shear centre and warping constant.

        Warping ordinate (unit warping), pole D, along a plate from a to b:

            d(omega) = (y_a - y_D)(z_b - z_D) - (y_b - y_D)(z_a - z_D)  -  psi * l / t

        The first part is twice the sector area swept from the pole. psi is the
        circulating shear flow of a closed cell per unit G*theta' (zero for open
        walls); it makes omega single valued around every cell.

        The shear centre M is the pole for which omega is orthogonal to y and z.
        """
        topo = self._topology()
        P = self._principal_nodes()
        A = self.total_area
        elems = self.elements

        # --- closed cells: Bredt.  F q = 2 A_cell ---
        cycles = topo["cycles"]
        twice_area = [sum(P[u][0]*P[v][1] - P[v][0]*P[u][1] for u, v in c["steps"]) for c in cycles]
        q = _solve(self._cell_matrix(topo), twice_area) if cycles else []
        psi = {e.element_id: 0.0 for e in elems}
        for c, qi in zip(cycles, q):
            for eid, s in c["sigma"].items():
                psi[eid] += qi * s

        I_T_open = sum(e.length * e.thickness**3 / 3 for e in elems)
        I_T_closed = sum(qi * w for qi, w in zip(q, twice_area))

        def warping(pole_y, pole_z):
            w = {topo["root"]: 0.0}
            for nid in topo["order"][1:]:
                u, e = topo["parent"][nid]
                yu, zu = P[u]
                yv, zv = P[nid]
                direction = 1.0 if e.start_node.id == u else -1.0
                w[nid] = (w[u] + (yu - pole_y)*(zv - pole_z) - (yv - pole_y)*(zu - pole_z)
                          - psi[e.element_id] * direction * e.length / e.thickness)
            mean = sum(e.area * (w[e.start_node.id] + w[e.end_node.id]) / 2 for e in elems) / A
            return {nid: value - mean for nid, value in w.items()}

        def mixed(w, component):
            total = 0.0
            for e in elems:
                ca, cb = P[e.start_node.id][component], P[e.end_node.id][component]
                wa, wb = w[e.start_node.id], w[e.end_node.id]
                total += e.area / 6 * (2*ca*wa + 2*cb*wb + ca*wb + cb*wa)
            return total

        def second(component):
            return sum(e.area / 3 * (P[e.start_node.id][component]**2
                                     + P[e.start_node.id][component] * P[e.end_node.id][component]
                                     + P[e.end_node.id][component]**2) for e in elems)

        I_z, I_y = second(0), second(1)
        tol = _REL_TOL * (I_y + I_z)

        w_c = warping(0.0, 0.0)                      # pole at the centre of gravity
        y_M = mixed(w_c, 1) / I_y if I_y > tol else 0.0
        z_M = -mixed(w_c, 0) / I_z if I_z > tol else 0.0

        omega = warping(y_M, z_M)
        I_omega = sum(e.area / 3 * (omega[e.start_node.id]**2
                                    + omega[e.start_node.id] * omega[e.end_node.id]
                                    + omega[e.end_node.id]**2) for e in elems)

        return {"topology": topo, "psi": psi, "I_T": I_T_open + I_T_closed,
                "I_T_open": I_T_open, "I_T_closed": I_T_closed,
                "y_M": y_M, "z_M": z_M, "omega": omega, "I_omega": I_omega,
                "I_y": I_y, "I_z": I_z}

    @property
    def I_T(self) -> float:
        """St. Venant torsion constant.

        Open walls contribute  l * t^3 / 3.  Closed cells add the Bredt part
        (4 * A_m^2 / integral(ds / t)  for a single cell).
        """
        return self._torsion()["I_T"]

    @property
    def I_omega(self) -> float:
        """Warping constant  I_omega = integral(omega^2 dA)  about the shear centre."""
        return self._torsion()["I_omega"]

    @property
    def shear_centre(self) -> tuple:
        """Shear centre (y_M, z_M) in the principal system."""
        result = self._torsion()
        return result["y_M"], result["z_M"]

    @property
    def shear_centre_1(self) -> tuple:
        """Shear centre (y1_M, z1_M) in the input system."""
        y_M, z_M = self.shear_centre
        a = math.radians(self.alpha)
        s, c = math.sin(a), math.cos(a)
        return self.Y1s + y_M*c - z_M*s, self.Z1s + y_M*s + z_M*c

    def warping_ordinates(self) -> dict:
        """Node id -> normalised warping ordinate omega about the shear centre.

        omega varies linearly along each plate.
        """
        return dict(self._torsion()["omega"])

    # ------------------------------------------------------------------
    # STATIC MOMENTS
    # ------------------------------------------------------------------

    def compute_static_moments(self, elements: list | None = None, n_pts: int = 50) -> dict:
        """Static moments S_y(s) and S_z(s) along every plate.

        S_y(s) = S_y0 + t * [z_a*s + (z_b - z_a)/(2l) * s^2]     (S_z likewise with y)

        Open walls start with S = 0 at their free ends. Where plates meet, the
        next plate starts with the sum of everything arriving at the node.
        In closed cells a constant is added per cell so that the section does
        not twist:  integral(S / t ds) = 0  around every cell.

        The shear flow from shear forces acting through the shear centre is then
        q(s) = -V_z*S_y(s)/I_y - V_y*S_z(s)/I_z, in the direction pv_start -> pv_end.

        Args:
            elements: Ignored, kept for backwards compatibility.
            n_pts: Number of samples per plate.

        Returns:
            dict: element_id -> {
                'pv_start': (y1, z1),  # start of the plotted direction, input system
                'pv_end'  : (y1, z1),  # end of the plotted direction, input system
                'start_node', 'end_node': node ids of those two points
                'reversed': True if that direction is opposite to the element's own
                's'  : list[float],    # arc-length samples [0 .. l]
                'Sy' : list[float],    # S_y at each sample
                'Sz' : list[float],    # S_z at each sample
            }
        """
        topo = self._topology()
        P = self._principal_nodes()
        adj, parent, order, cycles = topo["adj"], topo["parent"], topo["order"], topo["cycles"]
        F = self._cell_matrix(topo) if cycles else []
        n_pts = max(int(n_pts), 2)

        # Plot each tree plate from the leaf side towards the root.
        reversed_ = {e.element_id: False for e in self.elements}
        for nid in order[1:]:
            p = parent[nid][1]
            reversed_[p.element_id] = p.start_node.id != nid

        results = {}
        for e in self.elements:
            rev = reversed_[e.element_id]
            first, last = (e.end_node, e.start_node) if rev else (e.start_node, e.end_node)
            results[e.element_id] = {
                "pv_start": (first.y1, first.z1), "pv_end": (last.y1, last.z1),
                "start_node": first.id, "end_node": last.id, "reversed": rev,
                "s": [e.length * i / (n_pts - 1) for i in range(n_pts)],
            }

        for key, component in (("Sy", 1), ("Sz", 0)):
            ca = {e.element_id: P[e.start_node.id][component] for e in self.elements}
            cb = {e.element_id: P[e.end_node.id][component] for e in self.elements}
            gain = {e.element_id: e.area * (ca[e.element_id] + cb[e.element_id]) / 2 for e in self.elements}

            # Flow at the start of each plate, in the plate's own direction.
            Q0 = {cut.element_id: 0.0 for cut in topo["cuts"]}

            def inflow(e, nid):
                if e.end_node.id == nid:
                    return Q0[e.element_id] + gain[e.element_id]
                return -Q0[e.element_id]

            for nid in reversed(order[1:]):               # leaves first
                p = parent[nid][1]
                arriving = sum(inflow(e, nid) for e in adj[nid] if e is not p)
                if p.start_node.id == nid:
                    Q0[p.element_id] = arriving
                else:
                    Q0[p.element_id] = -arriving - gain[p.element_id]

            if cycles:
                elems = {e.element_id: e for e in self.elements}
                rhs = []
                for c in cycles:
                    total = 0.0
                    for eid, sigma in c["sigma"].items():
                        e = elems[eid]
                        integral = Q0[eid]*e.length + e.thickness * e.length**2 * (2*ca[eid] + cb[eid]) / 6
                        total += sigma * integral / e.thickness
                    rhs.append(-total)
                for c, constant in zip(cycles, _solve(F, rhs)):
                    for eid, sigma in c["sigma"].items():
                        Q0[eid] += constant * sigma

            for e in self.elements:
                eid, L, t = e.element_id, e.length, e.thickness
                values = [Q0[eid] + t * (ca[eid]*s + (cb[eid] - ca[eid]) / (2*L) * s**2)
                          for s in results[eid]["s"]]
                if reversed_[eid]:
                    values = [-v for v in reversed(values)]
                results[eid][key] = values

        return results

    # ------------------------------------------------------------------
    # STRESSES
    # ------------------------------------------------------------------

    def compute_stresses(self, N: float = 0.0, My: float = 0.0, Mz: float = 0.0,
                         Vy: float = 0.0, Vz: float = 0.0, Mx: float = 0.0,
                         Mw: float = 0.0, n_pts: int = 50) -> dict:
        """Stresses along every plate for a set of internal forces.

        Any consistent unit set works. With lengths in cm, use kN and kNcm to
        get stresses in kN/cm^2. All quantities refer to the principal axes;
        shear forces act through the shear centre.

            sigma_x = N/A + My/I_y * z - Mz/I_z * y + Mw/I_omega * omega
            tau     = -(Vz*S_y/I_y + Vy*S_z/I_z) / t        shear forces
                      + Mx * psi / (I_T * t)                torsion, closed cells
            tau_t   = |Mx| * t / I_T                        torsion, open walls
                                                            (peak value at the surface)

        Args:
            N: Axial force (tension positive).
            My, Mz: Bending moments about the principal axes.
            Vy, Vz: Shear forces.
            Mx: St. Venant (primary) torsion moment.
            Mw: Warping bimoment.
            n_pts: Number of samples per plate.

        Returns:
            dict: element_id -> the keys of ``compute_static_moments`` plus
                'sigma'      list[float]  normal stress
                'tau'        list[float]  shear stress in the direction pv_start -> pv_end
                'tau_t'      float        extra torsion shear stress at the plate surfaces
                'von_mises'  list[float]  sqrt(sigma^2 + 3*(|tau| + tau_t)^2)
        """
        tors = self._torsion()
        profiles = self.compute_static_moments(n_pts=n_pts)
        P = self._principal_nodes()
        A = self.total_area
        I_y, I_z, I_T, I_w = tors["I_y"], tors["I_z"], tors["I_T"], tors["I_omega"]
        omega = tors["omega"]
        tol = _REL_TOL * (I_y + I_z)

        def ratio(load, stiffness, limit):
            return load / stiffness if stiffness > limit else 0.0

        n_a = ratio(N, A, 0.0)
        m_y, m_z = ratio(My, I_y, tol), ratio(Mz, I_z, tol)
        v_y, v_z = ratio(Vy, I_z, tol), ratio(Vz, I_y, tol)
        m_x = ratio(Mx, I_T, 0.0)
        # I_omega has the unit length^6; compare it with (I_y + I_z) * A.
        m_w = ratio(Mw, I_w, 1e-9 * (I_y + I_z) * A)

        for e in self.elements:
            prof = profiles[e.element_id]
            a, b = prof["start_node"], prof["end_node"]
            count = len(prof["s"])
            psi = -tors["psi"][e.element_id] if prof["reversed"] else tors["psi"][e.element_id]

            sigma, tau = [], []
            for i in range(count):
                r = i / (count - 1)
                y = P[a][0] + (P[b][0] - P[a][0]) * r
                z = P[a][1] + (P[b][1] - P[a][1]) * r
                w = omega[a] + (omega[b] - omega[a]) * r
                sigma.append(n_a + m_y*z - m_z*y + m_w*w)
                tau.append((-v_z*prof["Sy"][i] - v_y*prof["Sz"][i] + m_x*psi) / e.thickness)

            tau_t = abs(m_x) * e.thickness
            prof["sigma"] = sigma
            prof["tau"] = tau
            prof["tau_t"] = tau_t
            prof["von_mises"] = [math.sqrt(s**2 + 3*(abs(t_) + tau_t)**2) for s, t_ in zip(sigma, tau)]

        return profiles


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _solve(matrix: list, rhs: list) -> list:
    """Solve a small dense linear system by Gaussian elimination."""
    n = len(rhs)
    a = [list(row) + [rhs[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-300:
            raise ValueError("The closed cells of the cross-section could not be resolved.")
        a[col], a[pivot] = a[pivot], a[col]
        for row in range(col + 1, n):
            factor = a[row][col] / a[col][col]
            for k in range(col, n + 1):
                a[row][k] -= factor * a[col][k]
    x = [0.0] * n
    for row in range(n - 1, -1, -1):
        x[row] = (a[row][n] - sum(a[row][k] * x[k] for k in range(row + 1, n))) / a[row][row]
    return x


def _plastic_modulus(plates: list) -> float:
    """integral(|c - c0| dA) about the axis c0 that halves the area.

    ``plates`` holds (c_start, c_end, area) per plate, with c varying linearly.
    """
    total = sum(area for _, _, area in plates)
    if total <= 0:
        return 0.0

    def area_below(c0):
        below = 0.0
        for ca, cb, area in plates:
            lo, hi = min(ca, cb), max(ca, cb)
            if hi <= c0:
                below += area
            elif lo < c0:
                below += area * (c0 - lo) / (hi - lo)
        return below

    lo = min(min(ca, cb) for ca, cb, _ in plates)
    hi = max(max(ca, cb) for ca, cb, _ in plates)
    for _ in range(200):
        mid = (lo + hi) / 2
        if area_below(mid) < total / 2:
            lo = mid
        else:
            hi = mid
    c0 = (lo + hi) / 2

    modulus = 0.0
    for ca, cb, area in plates:
        da, db = ca - c0, cb - c0
        if da * db >= 0:
            modulus += area * abs(da + db) / 2
        else:
            modulus += area * (da**2 + db**2) / (2 * (abs(da) + abs(db)))
    return modulus
