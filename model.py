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
    
    