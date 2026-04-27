import math
import numpy as np


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
    def __init__(self,thickness):
        """Initialize a CrossSection with uniform thickness.
        
        Args:
            thickness: Thickness of all elements in the cross-section.
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
        if self.total_area == 0:
            return 0.0
        return sum(e.Ayy_1i for e in self.elements)
    
    @property
    def A_zz_1(self) -> float:
        if self.total_area == 0:
            return 0.0
        return sum(e.Azz_1i for e in self.elements)
    
    @property
    def A_yz_1(self) -> float:
        if self.total_area == 0:
            return 0.0
        return sum(e.Ayz_1i for e in self.elements)
    
    
    #TRANSFORMATION OF COORDINATE SYSTEM CENTRE TO COG
    
    @property
    def Ayz_2(self) -> float:
        """Calculate Ayz_2"""
        if self.total_area == 0:
            return 0.0
        return self.A_yz_1 - self.Y1s*self.Z1s*self.total_area
    
    @property
    def Ayy_2(self) -> float:
        """Calculate Ayz_2"""
        if self.total_area == 0:
            return 0.0
        return self.A_yy_1 - (self.Y1s**2)*self.total_area
    
    @property
    def Azz_2(self) -> float:
        """Calculate Ayz_2"""
        if self.total_area == 0:
            return 0.0
        return self.A_zz_1 - (self.Z1s**2)*self.total_area
    
    #CALCULATIG ALPHA
    
    @property
    def alpha(self) -> float:
        if self.Azz_2 and self.Ayy_2 == 0:
            return 0.0
        return (math.degrees(math.atan((2*self.Ayz_2)/(self.Ayy_2 - self.Ayz_2))))/2
    
    #CALCULATING MOMENTS OF INERTIA
    
    @property
    def I_y(self) -> float:
        return self.Azz_2*(math.cos(self.alpha)**2) + self.Azz_2*(math.sin(self.alpha)**2) + 2*self.Ayz_2*math.sin(self.alpha)*math.cos(self.alpha)
    
    @property
    def I_z(self) -> float:
        return self.Ayy_2*(math.cos(self.alpha)**2) + self.Ayy_2*(math.sin(self.alpha)**2) + 2*self.Ayz_2*math.sin(self.alpha)*math.cos(self.alpha)
   
    #TRANSFORMATION FROM ARBITRARY SELECTED COS TO COG CENTERED COORDINATE SYSTEM
    
    def y(self, y_coordinate, z_coordinate) -> float:
        """Transform y coordinate to COG-centered coordinate system."""
        return (y_coordinate - self.Y1s)*math.cos(math.radians(self.alpha)) + (z_coordinate - self.Z1s)*math.sin(math.radians(self.alpha))
    
    def z(self, y_coordinate, z_coordinate) -> float:
        """Transform z coordinate to COG-centered coordinate system."""
        return (z_coordinate - self.Z1s)*math.cos(math.radians(self.alpha)) - (y_coordinate - self.Y1s)*math.sin(math.radians(self.alpha))

    def compute_static_moments(self, elements: list, n_pts: int = 50) -> dict:
        """Traverse an open thin-walled cross-section from free ends (S=0)
        and return parabolic Sy(s) and Sz(s) profiles for every element.

        S_y(s) = S_y0 + t * [z_from*s + (z_to - z_from)/(2L) * s^2]
        S_z(s) = S_z0 + t * [y_from*s + (y_to - y_from)/(2L) * s^2]

        Returns:
            dict: element_id -> {
                'pv_start': (y1, z1),  # traversal start coords in original CS
                'pv_end'  : (y2, z2),  # traversal end   coords in original CS
                's'  : np.array,       # arc-length samples [0 .. L]
                'Sy' : list[float],    # S_y values at each sample
                'Sz' : list[float],    # S_z values at each sample
            }
        """
        # --- adjacency: node_id -> [element, ...] ---
        adj: dict[int, list] = {}
        for elem in elements:
            for nid in (elem.start_node.id, elem.end_node.id):
                adj.setdefault(nid, [])
                if elem not in adj[nid]:
                    adj[nid].append(elem)

        # --- free ends: nodes connected to exactly one element -> S = 0 ---
        free_ends = [nid for nid, elems in adj.items() if len(elems) == 1]

        # BFS to propagate S values through nodes
        node_Sy: dict[int, float] = {nid: 0.0 for nid in free_ends}
        node_Sz: dict[int, float] = {nid: 0.0 for nid in free_ends}
        elem_meta: dict[int, dict] = {}   # element_id -> {Sy0, Sz0, rev, pv_start, pv_end}
        visited = set(free_ends)
        queue   = list(free_ends)

        while queue:
            cur = queue.pop(0)
            for elem in adj[cur]:
                if elem.element_id in elem_meta:
                    continue

                rev = (elem.start_node.id != cur)
                n_from = elem.end_node   if rev else elem.start_node
                n_to   = elem.start_node if rev else elem.end_node

                y_from_t = self.y(n_from.y1, n_from.z1)
                z_from_t = self.z(n_from.y1, n_from.z1)
                y_to_t   = self.y(n_to.y1,   n_to.z1)
                z_to_t   = self.z(n_to.y1,   n_to.z1)

                L = elem.length
                t = elem.thickness
                # Total increment across this element
                Sy_delta = t * (z_from_t * L + (z_to_t - z_from_t) * L / 2)
                Sz_delta = t * (y_from_t * L + (y_to_t - y_from_t) * L / 2)

                elem_meta[elem.element_id] = {
                    'Sy0'     : node_Sy[cur],
                    'Sz0'     : node_Sz[cur],
                    'rev'     : rev,
                    'pv_start': (n_from.y1, n_from.z1),
                    'pv_end'  : (n_to.y1,   n_to.z1),
                }

                if n_to.id not in visited:
                    node_Sy[n_to.id] = node_Sy[cur] + Sy_delta
                    node_Sz[n_to.id] = node_Sz[cur] + Sz_delta
                    visited.add(n_to.id)
                    queue.append(n_to.id)

        # --- Build parabolic profiles ---
        results = {}
        for elem in elements:
            meta = elem_meta.get(elem.element_id, {})
            Sy0  = meta.get('Sy0', 0.0)
            Sz0  = meta.get('Sz0', 0.0)
            rev  = meta.get('rev', False)

            n_from = elem.end_node   if rev else elem.start_node
            n_to   = elem.start_node if rev else elem.end_node

            y1_t = self.y(n_from.y1, n_from.z1)
            z1_t = self.z(n_from.y1, n_from.z1)
            y2_t = self.y(n_to.y1,   n_to.z1)
            z2_t = self.z(n_to.y1,   n_to.z1)

            L = elem.length
            t = elem.thickness
            s_arr = np.linspace(0.0, L, n_pts)
            Sy_arr = [Sy0 + t * (z1_t * s + (z2_t - z1_t) / (2 * L) * s ** 2) for s in s_arr]
            Sz_arr = [Sz0 + t * (y1_t * s + (y2_t - y1_t) / (2 * L) * s ** 2) for s in s_arr]

            results[elem.element_id] = {
                'pv_start': meta.get('pv_start', (n_from.y1, n_from.z1)),
                'pv_end'  : meta.get('pv_end',   (n_to.y1,   n_to.z1)),
                's'       : s_arr,
                'Sy'      : Sy_arr,
                'Sz'      : Sz_arr,
            }

        return results