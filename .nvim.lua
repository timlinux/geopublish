-- SPDX-FileCopyrightText: 2026 Kartoza
-- SPDX-License-Identifier: MIT
local wk = require("which-key")

wk.add({
  { "<leader>p", group = "geopublish" },
  { "<leader>pr", "<cmd>!geopublish --help<cr>", desc = "Run geopublish --help" },
  { "<leader>pt", "<cmd>!nix run .#test<cr>", desc = "Run tests" },
  { "<leader>pd", "<cmd>!nix run .#docs<cr>", desc = "Serve docs" },
  { "<leader>pf", "<cmd>!nix run .#format<cr>", desc = "Format code" },
  { "<leader>pl", "<cmd>!nix run .#lint<cr>", desc = "Lint code" },
})
