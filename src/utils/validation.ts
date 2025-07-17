import { z } from "zod";

export const pasteSchema = z.object({
  code: z.string().min(1, "Code is required"),
  filename: z.string().min(1, "Filename is required"),
});

export const zipSchema = z.object({
  zip: z.instanceof(File),
});

export const githubSchema = z.object({
  github_url: z.string().url().regex(/^https:\/\/github.com\//, "Must be a GitHub URL"),
}); 