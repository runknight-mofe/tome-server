Need a thin client.  Purpose is hands on mock testing of mofe capability set.  
Client requires the creation of the Mesh as a managed construct, complete with:

* Identifying information

* Join / leave capability (membership)

* Communication with a persistent Aether API service endpoint (defined separately)

  - Only node flagged and authenticated as admin can connect to the API.  By default, it is the ROOT anchor

  - Authenticated node acts as gateway and connection to API

* Wraps a MOFE Runtime to manage nodes and coordinate frame



Design:

* Remotely connect to a mesh

* Remotely manage a mesh

  - Connecting to existing UWB capable devices, either real or emulated

  - Managing mesh node membership; manage node identities and types

  - Managing mesh predicates

  - Viewing and managing mesh events

  - Managing mesh metadata / identifying information

* Create, remove, and modify predicates (geometric shapes).  Allow visual manipulation in the UI





Web client (JS / html / nginx); 

  - Utilize d3js or equivalent for visualizing the mesh, nodes, and predicates.  

  -  Interactive for efficient addition, changing, and removing of nodes and geometric predicates.  Examples:  moving or extending length of a line predicate; changing extents of a box; increasing or decreasing radius of a circle or sphere

  - Interactive for simple manipulation of location and gyro output of emulated devices (orientation, acceleration)

  -  UI/UX 

    - Focus layout on the topology grid.  

    - Tapping/clicking nodes or predicates selects them.  

    - Have a dedicated space for showing mesh object information as well as options for managing the object.  

    - For desktop, mousing over a mesh object (node, predicate) gives a rollup of its information.

    - For mobile, make it function in both portrait and landscape.  Make the elements scale and move to depending on zoon and orientation to avoid cluttering the mesh grid layout.

  - Produce telemetry.  Pushes data to configured Loki endpoint via API endpoint.  Organize dashboards for:

    - Overall topology health; including events

    - Per Node



Aether API / data model (Python / marshmallow / flask / psycopg2)

  - Contract for remotely interfacing with a mesh

  - Communicates with the designated gateway node to gather mesh data and remotely manage the mesh

  - Allows for remote management of meshes through well structured contract.

  - Allows persistence of mesh configuration and data to a global backend (eg postgresql).  Elements of a mesh not dependent on temporal data such as node spatial data can be re-created or reset to a state.  Attempts to re-add nodes to mesh if they are able (running the client on mobile device)



Data backend (postgresql)

  - Mesh identification and metadata

  - mesh states