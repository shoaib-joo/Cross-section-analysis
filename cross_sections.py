#This file contains the dictionary of cross section and their respective element connections



cross_sections = {"Custom":[[9.5,0],[5,0],[-5,0],[-9.5,0],[-9.5,18.65],[9.5,18.65]],  # (z,y) ordered pairs
                  "I-Section" : [[5,0],[0,0],[-5,0],[-5,10],[0,10],[5,10]],
                  "Channel" : [[0,0],[5,0],[5,10],[0,10]]          
                  
                  } 

element_connections = { "Custom": [(1, 2), (3, 4),(4,5) ,(5,6), (6,1),] ,
                        "I-Section" : [(1,2),(2,3),(2,5),(4,5),(5,6)],
                        "Channel" : [(1,2),(1,4),(4,3)]
                       
                    }

