/**
 * Aether Mesh - Zustand Store
 * Centralized state management for mesh, nodes, predicates, and events
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/react';

// Type definitions
export interface Vector3D {
  x: number;
  y: number;
  z: number;
}

export interface Quaternion {
  qx: number;
  qy: number;
  qz: number;
  qw: number;
}

export interface Node {
  id: string;
  mesh_id: string;
  type: 'anchor' | 'client';
  role: 'member' | 'gateway' | 'admin' | 'root';
  position: Vector3D;
  orientation: Quaternion;
  acceleration: Vector3D;
  status: 'online' | 'offline' | 'degraded' | 'error';
  signal_quality: number;
  rssi: number;
  is_admin: boolean;
  is_root: boolean;
  is_emulated: boolean;
  last_seen?: string;
  joined_at: string;
  metadata?: Record<string, any>;
}

export interface Predicate {
  id: string;
  mesh_id: string;
  type: 'point' | 'line' | 'box' | 'circle' | 'sphere' | 'cylinder';
  position: Vector3D;
  geometry: Record<string, any>;
  hysteresis: number;
  event_type?: string;
  event_id?: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface MeshEvent {
  id: string;
  mesh_id: string;
  source: 'user' | 'runtime' | 'system' | 'api';
  event_type: string;
  severity: 'debug' | 'info' | 'warn' | 'error' | 'critical';
  predicate_id?: string;
  node_id?: string;
  triggered_by_node_id?: string;
  event_data?: Record<string, any>;
  message?: string;
  timestamp: string;
  duration_ms?: number;
  request_id?: string;
}

export interface Mesh {
  id: string;
  name: string;
  description?: string;
  status: 'active' | 'archived' | 'deleted' | 'suspended';
  operating_mode: 'unknown' | 'minimal' | 'quorum' | 'calibration';
  root_node_id?: string;
  anchor_count: number;
  client_count: number;
  online_count: number;
  offline_count: number;
  average_signal_quality?: number;
  gdop?: number;
  updateFrequency?: number;
  created_at: string;
  updated_at: string;
  nodes?: Node[];
  predicates?: Predicate[];
}

export interface MeshStoreState {
  // Mesh state
  meshes: Mesh[];
  currentMesh: Mesh | null;
  currentMeshId: string | null;
  loading: boolean;
  error: string | null;

  // Node state
  nodes: Node[];
  selectedNode: Node | null;
  nodeFilter: {
    type?: 'anchor' | 'client';
    status?: 'online' | 'offline' | 'degraded' | 'error';
  };

  // Predicate state
  predicates: Predicate[];
  selectedPredicate: Predicate | null;

  // Event state
  events: MeshEvent[];
  eventFilter: {
    type?: string;
    severity?: string;
    node_id?: string;
  };

  // UI state
  viewMode: 'topology' | 'nodes' | 'predicates' | 'events';
  sidebarOpen: boolean;
  detailsPanelOpen: boolean;

  // Actions - Mesh
  setCurrentMesh: (mesh: Mesh | null) => void;
  setMeshes: (meshes: Mesh[]) => void;
  addMesh: (mesh: Mesh) => void;
  updateMesh: (mesh: Mesh) => void;
  deleteMesh: (meshId: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Actions - Nodes
  setNodes: (nodes: Node[]) => void;
  addNode: (node: Node) => void;
  updateNode: (node: Node) => void;
  removeNode: (nodeId: string) => void;
  setSelectedNode: (node: Node | null) => void;
  setNodeFilter: (filter: MeshStoreState['nodeFilter']) => void;

  // Actions - Predicates
  setPredicates: (predicates: Predicate[]) => void;
  addPredicate: (predicate: Predicate) => void;
  updatePredicate: (predicate: Predicate) => void;
  removePredicate: (predicateId: string) => void;
  setSelectedPredicate: (predicate: Predicate | null) => void;

  // Actions - Events
  setEvents: (events: MeshEvent[]) => void;
  addEvent: (event: MeshEvent) => void;
  prependEvent: (event: MeshEvent) => void; // Add to beginning of list
  clearOldEvents: (maxAge: number) => void; // Remove events older than maxAge ms
  setEventFilter: (filter: MeshStoreState['eventFilter']) => void;

  // Actions - UI
  setViewMode: (mode: MeshStoreState['viewMode']) => void;
  toggleSidebar: () => void;
  toggleDetailsPanel: () => void;

  // Computed/Derived
  filteredNodes: () => Node[];
  filteredEvents: () => MeshEvent[];
}

export const useMeshStore = create<MeshStoreState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    meshes: [],
    currentMesh: null,
    currentMeshId: null,
    loading: false,
    error: null,

    nodes: [],
    selectedNode: null,
    nodeFilter: {},

    predicates: [],
    selectedPredicate: null,

    events: [],
    eventFilter: {},

    viewMode: 'topology',
    sidebarOpen: true,
    detailsPanelOpen: true,

    // Mesh actions
    setCurrentMesh: (mesh) =>
      set({
        currentMesh: mesh,
        currentMeshId: mesh?.id || null,
        nodes: mesh?.nodes || [],
        predicates: mesh?.predicates || [],
      }),

    setMeshes: (meshes) => set({ meshes }),

    addMesh: (mesh) =>
      set((state) => ({
        meshes: [...state.meshes, mesh],
      })),

    updateMesh: (mesh) =>
      set((state) => ({
        meshes: state.meshes.map((m) => (m.id === mesh.id ? mesh : m)),
        currentMesh: state.currentMesh?.id === mesh.id ? mesh : state.currentMesh,
      })),

    deleteMesh: (meshId) =>
      set((state) => ({
        meshes: state.meshes.filter((m) => m.id !== meshId),
        currentMesh: state.currentMesh?.id === meshId ? null : state.currentMesh,
        currentMeshId: state.currentMeshId === meshId ? null : state.currentMeshId,
      })),

    setLoading: (loading) => set({ loading }),
    setError: (error) => set({ error }),

    // Node actions
    setNodes: (nodes) => set({ nodes }),

    addNode: (node) =>
      set((state) => ({
        nodes: [...state.nodes, node],
      })),

    updateNode: (node) =>
      set((state) => ({
        nodes: state.nodes.map((n) => (n.id === node.id ? node : n)),
        selectedNode: state.selectedNode?.id === node.id ? node : state.selectedNode,
      })),

    removeNode: (nodeId) =>
      set((state) => ({
        nodes: state.nodes.filter((n) => n.id !== nodeId),
        selectedNode: state.selectedNode?.id === nodeId ? null : state.selectedNode,
      })),

    setSelectedNode: (node) => set({ selectedNode: node }),

    setNodeFilter: (filter) => set({ nodeFilter: filter }),

    // Predicate actions
    setPredicates: (predicates) => set({ predicates }),

    addPredicate: (predicate) =>
      set((state) => ({
        predicates: [...state.predicates, predicate],
      })),

    updatePredicate: (predicate) =>
      set((state) => ({
        predicates: state.predicates.map((p) => (p.id === predicate.id ? predicate : p)),
        selectedPredicate:
          state.selectedPredicate?.id === predicate.id ? predicate : state.selectedPredicate,
      })),

    removePredicate: (predicateId) =>
      set((state) => ({
        predicates: state.predicates.filter((p) => p.id !== predicateId),
        selectedPredicate:
          state.selectedPredicate?.id === predicateId ? null : state.selectedPredicate,
      })),

    setSelectedPredicate: (predicate) => set({ selectedPredicate: predicate }),

    // Event actions
    setEvents: (events) => set({ events }),

    addEvent: (event) =>
      set((state) => ({
        events: [...state.events, event],
      })),

    prependEvent: (event) =>
      set((state) => ({
        events: [event, ...state.events],
      })),

    clearOldEvents: (maxAge) =>
      set((state) => {
        const now = Date.now();
        return {
          events: state.events.filter((e) => {
            const eventTime = new Date(e.timestamp).getTime();
            return now - eventTime < maxAge;
          }),
        };
      }),

    setEventFilter: (filter) => set({ eventFilter: filter }),

    // UI actions
    setViewMode: (mode) => set({ viewMode: mode }),
    toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
    toggleDetailsPanel: () => set((state) => ({ detailsPanelOpen: !state.detailsPanelOpen })),

    // Computed properties
    filteredNodes: () => {
      const state = get();
      const { nodes, nodeFilter } = state;
      return nodes.filter((node) => {
        if (nodeFilter.type && node.type !== nodeFilter.type) return false;
        if (nodeFilter.status && node.status !== nodeFilter.status) return false;
        return true;
      });
    },

    filteredEvents: () => {
      const state = get();
      const { events, eventFilter } = state;
      return events.filter((event) => {
        if (eventFilter.type && event.event_type !== eventFilter.type) return false;
        if (eventFilter.severity && event.severity !== eventFilter.severity) return false;
        if (eventFilter.node_id && event.node_id !== eventFilter.node_id) return false;
        return true;
      });
    },
  }))
);

// Selector hooks for better performance
export const useMeshSelector = () => useMeshStore((state) => state.currentMesh);
export const useNodesSelector = () => useMeshStore((state) => state.nodes);
export const usePredicatesSelector = () => useMeshStore((state) => state.predicates);
export const useEventsSelector = () => useMeshStore((state) => state.events);
export const useLoadingSelector = () => useMeshStore((state) => state.loading);
export const useErrorSelector = () => useMeshStore((state) => state.error);
