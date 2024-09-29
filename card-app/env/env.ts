"use server";

export const getEnv = async () => ({
  API_URL: process.env.API_URL || 'http://localhost:8000',
});