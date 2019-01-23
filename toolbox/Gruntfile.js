module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    // Task configuration goes here.
    uglify: {
      app: {
        files: {'build/static/js/app.min.js': ['toolbox/static/js/app/**/*.js']}
      },
      vendor: {
        files: {'build/static/js/lib.min.js': ['toolbox/static/js/vendor/**/*.js']}
      }
    },

    sass: {
      dev: {
        options: {
          includePaths: ['bower_components/foundation/scss']
        },
        files: {
          'build/static/css/screen.css': 'toolbox/static/scss/screen.scss'
        }
      },
      deploy: {
        options: {
          includePaths: ['bower_components/foundation/scss'],
          outputStyle: 'compressed'
        },
        files: {
          'build/static/css/screen.min.css': 'toolbox/static/scss/screen.scss'
        }
      }
    },

    less: {
      dev: {
        options: {
          paths: ['toolbox/static/less']
        },
        files: {
          'build/static/css/screen.css': 'toolbox/static/less/screen.less'
        }
      },
      deploy: {
        options: {
          paths: ['toolbox/static/less'],
            compress: true
          },
          files: {
            'build/static/css/screen.min.css': 'toolbox/static/less/screen.less'
          }
        }
      },

      watch: {
        options: {livereload: true}
        javascript: {
          files: ['toolbox/static/js/app/**/*.js'],
          tasks: ['concat']
        },
        sass: {
          files: 'toolbox/static/scss/**/*.scss',
          tasks: ['sass:dev']
        }
      }

  });

  // Load plugins here.
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-sass');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-watch');

  // Register tasks here.
  grunt.registerTask('default', []);

};
