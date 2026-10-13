// A value React components can watch (get, set, subscribe): kept in localStorage, or only in memory.

import { useSyncExternalStore } from "react";

export type Store<T> = {
  get: () => T;
  set: (next: T | ((old: T) => T)) => void;
  subscribe: (listener: () => void) => () => void;
};

export function stored<T>(key: string, initial: T): Store<T> {
  let value = initial;
  try {
    const text = localStorage.getItem(key);
    if (text) value = { ...initial, ...JSON.parse(text) };
  } catch {
    // private window or bad JSON: start fresh
  }
  return memory(value, (next) => {
    try {
      localStorage.setItem(key, JSON.stringify(next));
    } catch {
      // full or blocked: keep it for this visit
    }
  });
}

export function memory<T>(initial: T, onSet: (value: T) => void = () => {}): Store<T> {
  let value = initial;
  const listeners = new Set<() => void>();
  return {
    get: () => value,
    set(next) {
      value = typeof next === "function" ? (next as (old: T) => T)(value) : next;
      onSet(value);
      listeners.forEach((listener) => listener());
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}

export function useStore<T>(store: Store<T>): T {
  return useSyncExternalStore(store.subscribe, store.get);
}
