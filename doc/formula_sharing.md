# Formula Sharing Proposal

I'd like to foster community by making it easier for Gnofract 4D users to share things that they have created (or discovered, if you like). This includes:

- Formulas and Coloring Algorithms
- Parameter files
- Possibly image? At least thumbnails, but maybe not high-res renders

## Requirements

- Sharing must be optional. The program can still be used entirely offline
- Sharing must be easy.
- It's more important to making consumption easy than publishing, because more people will consume than publish.

## Proposal

Fractal formulas and parameter files are source code, so they should be stored in a version control system. We're generally using Git, so that seems like the place to start. This is a powerful option,
but not without downsides. Git is not exactly trivial software for unsophisticated users to deal with,
so this is in tension with the goal that sharing should be easy. 

### Repository
We designate a central GitHub repository (github.com/fract4d/formulas) as the root. 
Within that repo, we establish the layout:

`stdlib/`

contains 'standard' formula files which ship with Gnofract 4D.

`orgform/`

contains saved formula files from Fractint's orgform database

`{username}/`

Within the repo, a folder matching the name of a GitHub user is 'owned' by that user. If user A wants to modify `A/myformula.frm` they should be able to do so without anyone else having to approve. If user B wants to modify `A/myformula.frm` they should be able to submit a PR and have user A review it and choose
whether to merge.

Initially changes can be merged by hand. Later a GitHub Action can take care of this behavior. When a PR is received, it can check that all the files modified are under a directory with the same name as the user who owns the fork it comes from, and auto-merge if so. 

### Startup Behavior and Read-Only Sharing

Gnofract 4D will still ship with a snapshot of the 'stdlib' formulas which existed at the time it was compiled, so it can be used without GitHub access.

But it will additionally maintain a local Git repo in a user-selectable directory, by default `~/gnofract4d-formulas`. On startup, if this 
directory does not contain a Git repo, user will be prompted "Would you like to download latest formulas?" [Yes/No/Don't ask again]. If yes, we'll run 'git clone' to populate that directory with the current 
contents of the shared formula repo. The directory search order will be such that we look in that directory first, before any directory we install, which allows newer versions to supercede the ones we
ship with. We can also display a non-blocking message 'new formulas downloaded!" 

A user can edit files stored in ~/.gnofract4d-formulas and we will modify the UX to make it easier to do that directly. TBD: Should the UX 'commit' changes locally, and if so when?

If user has opted in to downloading formulas, on subsequent starts we 'git pull'; in case of a merge conflict we display a warning and do nothing.

### Sharing

To contribute changed formulas back to the mothership, the user will need:
- A github account
- A fork of fract4d/formulas in their own GitHub account
- Create a PR to merge changes from their fork

In an initial version, we could just publish a doc on how to do that. It would be something like:
- Create a GitHub account, if needed
- Fork fract4d/formulas via the GitHub UX
- update the remote reference in their local repo to point to their fork
- Git push
- Create a PR

Later we can have a 'Share' option in the UX which streamlines this behavior.