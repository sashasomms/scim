# Sasha Sommerfeldt
# June 2022
# Make (for all participants): 
# Histograms of ibis for each phase of TSST,
# Scatterplots of ibis in order they occurred
# Plot of ECG timeseries with exclude sections (from processing notes) overlaid

# Clear the workspace ----------------------------------------------------------
rm(list=ls())

# Packages ---------------------------------------------------------------------
library(tidyverse)
library(sys)

# Directories ------------------------------------------------------------------
ddir = '../../processed-data/interoception/psychophys/'
outdir = '../../processed-data/interoception/psychophys/ecgQA/plots/'

# Get a participant list from the cmetx_output_ibis directory 
# Note this won't work if for some reason someone is missing the Recovery phase
participants_temp = Sys.glob(file.path(paste0(ddir, '41*_t[12]/cmetx_output_ibis/*HeartToneBlock2_R1.txt')))
# Think errors were because the ecgQA file wasnt updated
participants = participants_temp %>% basename() %>% str_remove('_interoception0000_ecgHeartToneBlock2_R1.txt')

for (p in participants) {
 print(p)
 pdir = paste0(ddir, p, '/cmetx_output_ibis/*.txt')
 pfiles = Sys.glob(file.path(pdir))
 print(pfiles)
 for (f in pfiles) {
   df = read_csv(f, col_names = F)
   r = range(df$X1)
   sd = sd(df$X1)
   fig_title = basename(f)
   outfile_name = basename(f) %>% str_replace(".txt", "_ibi_hist.png")
   print(outfile_name)
   hist_ibi = ggplot(df, aes(x = X1)) +
     geom_histogram(binwidth = 10, color = "black", fill = "#C70039") +
     labs(title = fig_title, x = "IBI (ms)", y = "Count") +
     theme_classic() +
     theme(text = element_text(size = 12))
   ggsave(filename = paste0(outdir, outfile_name), plot = hist_ibi, width = 6, height = 6)
 }
}
# Overwrite with clean ones where applicable
for (p in participants) {
 print(p)
 pdir = paste0(ddir, p, '/cmetx_output_ibis/*clean.txt')
 pfiles = Sys.glob(file.path(pdir))
 print(pfiles)
 for (f in pfiles) {
   df = read_csv(f, col_names = F)
   r = range(df$X1)
   sd = sd(df$X1)
   fig_title = basename(f)
   outfile_name = basename(f) %>% str_replace("_clean.txt", "_ibi_hist.png")
   print(outfile_name)
   hist_ibi = ggplot(df, aes(x = X1)) +
     geom_histogram(binwidth = 10, color = "black", fill = "#C70039") +
     labs(title = fig_title, x = "IBI (ms)", y = "Count") +
     theme_classic() +
     theme(text = element_text(size = 16))
   ggsave(filename = paste0(outdir, outfile_name), plot = hist_ibi, width = 6, height = 6)
 }
}


# Scatterplots with all IBIs ---------------------------------------------------

for (p in participants) {
  print(p)
  pdir = paste0(ddir, '/', p, '/cmetx_output_ibis/*.txt')
  pfiles = Sys.glob(file.path(pdir))
  print(pfiles)
  for (f in pfiles) {
    df = read_csv(f, col_names = F)
    # Convert rownames/index to column (will use as time var for place in timeseries)
    df = rownames_to_column(df, "index")
    
    # Make sure index is numeric
    df$index = as.numeric(df$index)
    
    fig_title = basename(f)
    outfile_name = basename(f) %>% str_replace(".txt", "_ibi_plot.png")
    print(outfile_name)
    plot_ibi = ggplot(df, aes(x = index, y = X1)) +
      geom_point(size = 1.5, alpha = .6) +
      theme_bw(base_size = 14) +  
      theme(panel.grid.minor = element_blank(),
            axis.line = element_line(color="black"),
            axis.ticks = element_line(color="black"),
            panel.border = element_blank())+
      labs(title = fig_title, x = "Order", y = "IBI")
    ggsave(filename = paste0(outdir, '/', outfile_name), plot = plot_ibi, width = 12, height = 4)
  }
}
# Overwrite with the clean ones 
for (p in participants) {
  print(p)
  pdir = paste0(ddir, '/', p, '/cmetx_output_ibis/*_clean.txt')
  pfiles = Sys.glob(file.path(pdir))
  print(pfiles)
  for (f in pfiles) {
    df = read_csv(f, col_names = F)
    # Convert rownames/index to column (will use as time var for place in timeseries)
    df = rownames_to_column(df, "index")
    # Convert index to numeric
    df$index = as.numeric(df$index)
    
    fig_title = basename(f)
    outfile_name = basename(f) %>% str_replace("_clean.txt", "_ibi_plot.png")
    print(outfile_name)
    plot_ibi = ggplot(df, aes(x = index, y = X1)) +
      geom_point(size = 1.5, alpha = .6) +
      theme_bw(base_size = 14) +  
      theme(panel.grid.minor = element_blank(),
            axis.line = element_line(color="black"),
            axis.ticks = element_line(color="black"),
            panel.border = element_blank())+
      labs(title = fig_title, x = "Order", y = "IBI")
    ggsave(filename = paste0(outdir, '/', outfile_name), plot = plot_ibi, width = 12, height = 4)
  }
}



# Plot with exclude sections over ECG data -------------------------------------
df_exclude = read_tsv(paste0(ddir, 'ecgQA/quality_notes/parsed/Exclude.txt'))
# replace xmin and xmax in annotate with exclude_sections
for (p in participants) {
  print(p)
  pdir = paste0(ddir, p, '/ecg_by_block/*Block*')
  pfiles = Sys.glob(file.path(pdir))
  print(pfiles)
  for (f in pfiles) {
    # Plot ECG
    df_ECG = read_tsv(f, col_names = F) %>% dplyr::rename(c('time' = 'X1', 'ecg' = 'X2'))
    fig_title = basename(f)
    plot_ecg = ggplot(df_ECG, aes(x = time, y = ecg)) +
      geom_line() +
      theme_bw(base_size = 14) +  
      theme(panel.grid.minor = element_blank(),
            axis.line = element_line(color="black"),
            axis.ticks = element_line(color="black"),
            panel.border = element_blank()) +
      labs(title = fig_title, x = "Time", y = "ECG")
    
    # Overlay Exclude sections
    split_basename = basename(f) %>% str_split('_', simplify = T)
    phase = split_basename[4] %>% substring(4)
    df_exclude_p = df_exclude[df_exclude$Subject_Timepoint == p, ] %>% select(contains(c(phase)))
    # If exclude sections is not empty -- so there is a section to exclude
    if (length(df_exclude_p) != 0) {
      split_exclude_ref = df_exclude_p[1,1] %>% str_split(',', simplify = T)
      # Then for each section noted to exclude
      for (section in split_exclude_ref) {
        # Get the start and stop times
        start_stop = section %>% str_split('-', simplify = T)
        # Add a layer to the plot with that section as a rectangle
        plot_ecg = plot_ecg + annotate("rect", xmin = as.numeric(start_stop[1]), xmax = as.numeric(start_stop[2]), ymin = -.5, ymax = 1,
                                       alpha = .5, fill = "red")
      }
    }
    # Save the final plot with overlays (or without overlays if no exclude sections were noted)
    outfile_name = basename(f) %>% str_replace("12s.txt", "exclude_plot.png")
    ggsave(filename = paste0(outdir, '/', outfile_name), plot = plot_ecg, width = 20, height = 4)
  }
}





