const path = require('path');

module.exports = {
  mode: 'production',
  entry: './src/module.ts',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'module.js',
    libraryTarget: 'amd',
    clean: true,
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx'],
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: {
          loader: 'ts-loader',
          options: {
            transpileOnly: true,
            compilerOptions: {
              noEmit: false,
            },
          },
        },
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
      },
      {
        test: /\.(png|jpe?g|gif|svg)$/i,
        type: 'asset/resource',
      },
    ],
  },
  externals: [
    // Grafana libraries should be external
    'react',
    'react-dom',
    '@grafana/data',
    '@grafana/ui',
    '@grafana/runtime',
    'lodash',
    'moment',
  ],
  devtool: 'source-map',
};
